"""Tests for monogate.witness (folded in from eml-witness 0.2.0 in monogate 2.4.0)."""
from __future__ import annotations

import dataclasses as _dc
import json

import pytest
import sympy as sp

# Skip the entire module if the witness extra isn't installed.
pytest.importorskip("eml_cost")
pytest.importorskip("eml_discover")
pytest.importorskip("eml_rewrite")

from monogate.witness import (   # noqa: E402
    UniversalityWitness,
    WitnessIdentified,
    WitnessProfile,
    universality_witness,
    witness_to_dict,
    LEAN_UNIVERSALITY_URL,
)


x = sp.Symbol("x")
y = sp.Symbol("y")


def test_witness_for_canonical_sigmoid():
    w = universality_witness("1/(1+exp(-x))")
    assert isinstance(w, UniversalityWitness)
    assert w.input_expr_str == "1/(1 + exp(-x))"
    assert isinstance(w.profile, WitnessProfile)
    assert w.profile.pfaffian_r >= 1
    assert w.profile.predicted_depth >= 1
    assert w.profile.fingerprint.startswith("p")
    assert w.profile.axes.startswith("p")
    assert w.identified is not None
    assert isinstance(w.identified, WitnessIdentified)
    assert "sigmoid" in w.identified.name.lower()
    # Sigmoid is in the EML class — verified_in_lean is True.
    assert w.verified_in_lean is True
    assert w.lean_url == LEAN_UNIVERSALITY_URL


def test_witness_for_textbook_sigmoid_walks_to_canonical():
    w = universality_witness(sp.exp(x) / (1 + sp.exp(x)))
    assert len(w.canonical_path) >= 2
    costs = [step.cost for step in w.canonical_path]
    assert costs == sorted(costs, reverse=True)
    assert w.savings >= 1


def test_witness_for_pythagorean_collapses_to_one():
    w = universality_witness(sp.sin(x) ** 2 + sp.cos(x) ** 2)
    assert w.canonical_path
    final = w.canonical_path[-1]
    assert final.expression_str == "1"
    assert w.savings >= 1


def test_witness_pfaffian_not_eml_for_bessel():
    w = universality_witness(sp.besselj(0, x))
    assert w.profile.is_pfaffian_not_eml is True
    # Bessel is OUTSIDE the EML class — verified_in_lean stays False.
    assert w.verified_in_lean is False
    assert w.lean_url is None


# ---- 2.4.3 hotfix regression tests ---------------------------------
# Non-elementary functions the cost detector silently treats as
# depth-0 atoms (is_pfaffian_not_eml=False). Pre-2.4.3,
# verified_in_lean was wrongly True for them. The strict allow-list
# check fixes this.

def test_witness_erf_is_not_verified():
    w = universality_witness(sp.erf(x))
    assert w.verified_in_lean is False
    assert w.lean_url is None


def test_witness_gamma_is_not_verified():
    w = universality_witness(sp.gamma(x))
    assert w.verified_in_lean is False


def test_witness_polylog_is_not_verified():
    w = universality_witness(sp.polylog(2, x))
    assert w.verified_in_lean is False


def test_witness_elliptic_is_not_verified():
    w = universality_witness(sp.elliptic_k(x))
    assert w.verified_in_lean is False


def test_witness_compound_with_erf_is_not_verified():
    """Larger expression containing erf as a subterm fails the
    strict check (recursion case)."""
    w = universality_witness(sp.exp(x) + sp.erf(x))
    assert w.verified_in_lean is False


def test_witness_pi_and_e_atoms_are_in_class():
    """pi and E are atoms (NumberSymbol), not Functions — accepted."""
    w = universality_witness(sp.pi * x + sp.E)
    assert w.verified_in_lean is True
    assert w.lean_url is not None


def test_witness_to_dict_roundtrips_through_json():
    w = universality_witness("exp(sin(x))")
    d = witness_to_dict(w)
    s = json.dumps(d)
    roundtripped = json.loads(s)
    assert roundtripped["input_expr"] == "exp(sin(x))"
    assert "profile" in roundtripped
    assert "fingerprint" in roundtripped["profile"]
    assert "verified_in_lean" in roundtripped
    assert roundtripped["verified_in_lean"] is True   # in EML class
    assert roundtripped["lean_url"] is not None


def test_witness_dict_shape_matches_documented_keys():
    w = universality_witness("sin(x)")
    d = witness_to_dict(w)
    assert set(d.keys()) == {
        "input_expr", "profile", "identified",
        "canonical_path", "savings",
        "verified_in_lean", "lean_url",
    }


def test_walk_canonical_false_skips_path_walk():
    w = universality_witness(
        sp.exp(x) / (1 + sp.exp(x)),
        walk_canonical=False,
    )
    assert w.canonical_path == ()
    assert w.savings == 0


def test_explicit_canonical_target():
    w = universality_witness(
        sp.exp(x) / (1 + sp.exp(x)),
        canonical_target=1 / (1 + sp.exp(-x)),
    )
    assert w.canonical_path
    assert w.canonical_path[-1].expression_str == "1/(1 + exp(-x))"


def test_invalid_expression_raises_value_error():
    with pytest.raises(ValueError):
        universality_witness("not valid sympy ((((((")


def test_wrong_type_raises_type_error():
    with pytest.raises(TypeError):
        universality_witness(42)             # type: ignore[arg-type]


def test_witness_is_immutable():
    """frozen=True dataclass + tuple canonical_path → deeply immutable."""
    w = universality_witness("sin(x)")
    with pytest.raises(_dc.FrozenInstanceError):
        w.savings = 999          # type: ignore[misc]
    assert isinstance(w.canonical_path, tuple)
