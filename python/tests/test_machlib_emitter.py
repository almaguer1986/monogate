"""Tests for monogate.machlib_emitter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from monogate.machlib_emitter import (
    EmitConfig,
    EmitResult,
    emit_machlib_lean,
    tree_to_lean,
)


# ──────────────────────────────────────────────────────────────────
# Stub ProofResult: the emitter takes Any, so we don't depend on the
# real dataclass. This keeps tests fast and avoids import cycles.
# ──────────────────────────────────────────────────────────────────


@dataclass
class _FakeResult:
    status: str
    identity_str: str = "x*1 == x"
    witness_tree: Optional[dict] = None
    max_residual: float = 0.0
    sympy_simplification: Optional[str] = None


# ──────────────────────────────────────────────────────────────────
# tree_to_lean
# ──────────────────────────────────────────────────────────────────


def test_tree_to_lean_returns_var_for_x_leaf():
    assert tree_to_lean({"op": "leaf", "val": "x"}) == "x"


def test_tree_to_lean_renames_variable():
    out = tree_to_lean({"op": "leaf", "val": "x"}, var_name="y")
    assert out == "y"


def test_tree_to_lean_typed_numeric_leaf():
    out = tree_to_lean({"op": "leaf", "val": 1.0})
    assert out == "(1.0 : Real)"


def test_tree_to_lean_eml_node():
    tree = {
        "op": "eml",
        "left": {"op": "leaf", "val": "x"},
        "right": {"op": "leaf", "val": 1.0},
    }
    out = tree_to_lean(tree)
    assert "Real.exp" in out
    assert "Real.log" in out
    assert "x" in out
    assert "(1.0 : Real)" in out


def test_tree_to_lean_handles_none():
    assert tree_to_lean(None) == "sorry"


def test_tree_to_lean_handles_unknown_op():
    assert tree_to_lean({"op": "?"}) == "sorry"


# ──────────────────────────────────────────────────────────────────
# emit_machlib_lean: status branches
# ──────────────────────────────────────────────────────────────────


def test_emit_returns_none_for_failed_proof():
    r = _FakeResult(status="failed")
    assert emit_machlib_lean(r, theorem_name="x") is None


def test_emit_returns_none_for_inconclusive():
    r = _FakeResult(status="inconclusive")
    assert emit_machlib_lean(r, theorem_name="x") is None


def test_emit_proved_exact_uses_rfl_or_sorry():
    r = _FakeResult(
        status="proved_exact",
        identity_str="x*1 == x",
        sympy_simplification="0",
    )
    out = emit_machlib_lean(r, theorem_name="mul_one")
    assert out is not None
    assert out.proof_kind == "rfl_or_sorry"
    # `first | rfl | sorry` — accepts rfl when the goal is reflexive,
    # falls back to sorry so the file still compiles.
    assert "rfl" in out.code
    assert "sorry" in out.code
    assert "import MachLib.Basic" in out.code


def test_emit_proved_witness_emits_witness_def():
    tree = {
        "op": "eml",
        "left": {"op": "leaf", "val": "x"},
        "right": {"op": "leaf", "val": 1.0},
    }
    r = _FakeResult(
        status="proved_witness",
        identity_str="x == eml(x, 1)",
        witness_tree=tree,
        max_residual=1e-15,
    )
    out = emit_machlib_lean(r, theorem_name="eml_id")
    assert out is not None
    assert out.proof_kind == "sorry_witness"
    assert "noncomputable def witness_eml_id" in out.code
    assert "unfold witness_eml_id" in out.code
    assert "sorry" in out.code


def test_emit_proved_certified_uses_sorry_with_residual():
    r = _FakeResult(
        status="proved_certified",
        identity_str="x == x",
        max_residual=1e-12,
    )
    out = emit_machlib_lean(r, theorem_name="trivial_eq")
    assert out is not None
    assert out.proof_kind == "sorry_certified"
    assert "1.00e-12" in out.code or "residual 1.00e-12" in out.code
    assert "sorry" in out.code


def test_emit_proved_numerical_records_residual():
    r = _FakeResult(
        status="proved_numerical",
        identity_str="x*2 == x+x",
        max_residual=4.4e-9,
    )
    out = emit_machlib_lean(r, theorem_name="double_x")
    assert out is not None
    assert out.proof_kind == "sorry_certified"
    # 4.40e-09 in scientific format somewhere in the comment.
    assert "4.40e-09" in out.code


# ──────────────────────────────────────────────────────────────────
# emit_machlib_lean: shape / config
# ──────────────────────────────────────────────────────────────────


def test_emit_includes_all_machlib_imports_by_default():
    r = _FakeResult(status="proved_exact", sympy_simplification="0")
    out = emit_machlib_lean(r, theorem_name="t")
    for mod in ("Basic", "EML", "Trig", "Forge"):
        assert f"import MachLib.{mod}" in out.code


def test_emit_respects_custom_imports():
    r = _FakeResult(status="proved_exact", sympy_simplification="0")
    cfg = EmitConfig(machlib_imports=("MachLib.Basic",))
    out = emit_machlib_lean(r, theorem_name="t", config=cfg)
    assert "import MachLib.Basic" in out.code
    assert "import MachLib.EML" not in out.code
    assert "import MachLib.Trig" not in out.code


def test_emit_renames_variable():
    r = _FakeResult(status="proved_exact", sympy_simplification="0")
    cfg = EmitConfig(var_name="y")
    out = emit_machlib_lean(r, theorem_name="t", config=cfg)
    assert "(y : Real)" in out.code


def test_emit_uses_identity_str_override():
    r = _FakeResult(status="proved_exact", sympy_simplification="0",
                     identity_str="ignored")
    out = emit_machlib_lean(
        r, theorem_name="t", identity_str="x + 0 == x",
    )
    # Expect the overridden identity in the comment line, with == -> =.
    assert "x + 0 = x" in out.code


def test_emit_witness_def_can_be_disabled():
    tree = {"op": "leaf", "val": "x"}
    r = _FakeResult(
        status="proved_witness",
        witness_tree=tree,
        max_residual=1e-15,
    )
    cfg = EmitConfig(emit_witness_def=False)
    out = emit_machlib_lean(r, theorem_name="t", config=cfg)
    assert "noncomputable def witness_t" not in out.code


# ──────────────────────────────────────────────────────────────────
# Smoke: every emitted file ends with a newline + has both
# `theorem` and `:= by` (so the Lean parser at least sees a theorem).
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("status,extra", [
    ("proved_exact", {"sympy_simplification": "0"}),
    ("proved_witness", {
        "witness_tree": {"op": "leaf", "val": "x"},
        "max_residual": 1e-15,
    }),
    ("proved_certified", {"max_residual": 1e-12}),
    ("proved_numerical", {"max_residual": 1e-9}),
])
def test_emitted_files_are_well_formed(status, extra):
    r = _FakeResult(status=status, **extra)
    out = emit_machlib_lean(r, theorem_name="smoke_thm")
    assert out is not None
    assert out.code.endswith("\n")
    assert "theorem smoke_thm" in out.code
    assert ":= by" in out.code
