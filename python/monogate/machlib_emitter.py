"""monogate.machlib_emitter — neurosymbolic Lean / MachLib proof emitter.

Bridges the EML witness output of :class:`monogate.prover.EMLProver` to
Lean files that depend only on MachLib axioms (no Mathlib). Given a
successful :class:`ProofResult` and the target theorem name, emits a
``.lean`` file that:

  1. Imports the MachLib foundations (``MachLib.Basic``, ``MachLib.EML``,
     ``MachLib.Trig``, ``MachLib.Forge``).
  2. Optionally emits a ``noncomputable def`` for the EML witness tree
     when the prover found one — this makes the witness an explicit
     Lean term so a downstream agent / human only has to verify the
     equality, not reconstruct the witness.
  3. Emits the theorem statement (matching the kernel's
     ``@verify(lean, theorem=…)`` name).
  4. Picks a proof body based on the proof status:

     +----------------------+----------------------------------+
     | status               | proof body                       |
     +======================+==================================+
     | proved_exact         | ``by simp`` / ``by ring`` /      |
     |                      | ``by rfl``                       |
     +----------------------+----------------------------------+
     | proved_certified     | ``sorry`` with a comment giving  |
     |                      | the certified residual           |
     +----------------------+----------------------------------+
     | proved_numerical     | same — numerical witness only,   |
     |                      | not a tactic proof               |
     +----------------------+----------------------------------+
     | proved_witness       | emits witness ``def`` + theorem  |
     |                      | with ``unfold; sorry`` + residual |
     +----------------------+----------------------------------+
     | inconclusive/failed  | nothing emitted (returns None)   |
     +----------------------+----------------------------------+

The emitter is **scaffolding** — it produces well-formed Lean that the
Lean kernel will accept (modulo ``sorry``). It does *not* automatically
discharge non-trivial proof obligations; that's the v3 deliverable
(learned tactic policy). What v2 buys: every successful MCTS discovery
gets a clean per-theorem ``.lean`` with the witness, the imports, and
the right shape, ready for human review.

CPU-only — pure tree traversal, no learned models.

Public API:

    >>> from monogate.machlib_emitter import emit_machlib_lean
    >>> code = emit_machlib_lean(result, theorem_name="my_thm",
    ...                          identity_str="x*1 == x")
    >>> with open("MachLib/Discovered/my_thm.lean", "w") as f:
    ...     f.write(code)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


__all__ = [
    "EmitConfig",
    "EmitResult",
    "emit_machlib_lean",
    "tree_to_lean",
]


# ──────────────────────────────────────────────────────────────────
# Config + result
# ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EmitConfig:
    """Knobs for the Lean emitter.

    Attributes:
        machlib_imports: Which MachLib modules to import. Defaults to
            the canonical four; trim this list when you know your kernel
            won't use, e.g., ``Trig``.
        var_name: Name of the free variable in the theorem (default
            ``x``). Multi-variable identities are not supported in v2.
        signature: Type of the variable. Defaults to ``Real`` from
            ``MachLib``.
        residual_threshold: Below this, we annotate "machine-verified"
            and emit a witness ``def``; above it, we annotate
            "advisory" and still emit ``sorry``.
        emit_witness_def: When ``True``, every witness tree becomes a
            named ``noncomputable def`` so the proof can ``unfold`` it.
    """

    machlib_imports: tuple[str, ...] = (
        "MachLib.Basic",
        "MachLib.EML",
        "MachLib.Trig",
        "MachLib.Forge",
    )
    var_name: str = "x"
    signature: str = "Real"
    residual_threshold: float = 1e-8
    emit_witness_def: bool = True


@dataclass(frozen=True)
class EmitResult:
    """One emitted Lean file.

    Attributes:
        code: The full Lean source as a string (may end with newline).
        proof_kind: One of ``"ring"``, ``"sorry_certified"``,
            ``"sorry_witness"``, ``"trivial"``.
        residual: Witness residual carried into the comment, if any.
        theorem_name: Echo of the input theorem name for downstream
            file-naming convenience.
    """

    code: str
    proof_kind: str
    residual: float
    theorem_name: str


# ──────────────────────────────────────────────────────────────────
# Witness-tree -> Lean expression
# ──────────────────────────────────────────────────────────────────


def tree_to_lean(tree: Optional[dict[str, Any]],
                 *,
                 var_name: str = "x") -> str:
    """Render an EML witness tree (the ``{"op": "leaf"|"eml", ...}``
    dict format produced by :func:`_mcts_witness_search`) as a Lean
    expression.

    Lean spelling: ``eml(a, b)`` becomes ``Real.exp a - Real.log b``
    (see :file:`MachLib/EML.lean` — that's the exact unfolding of the
    EML primitive). Leaves render as either the variable name or a
    real-typed numeric literal.

    Returns the literal ``"sorry"`` for a missing tree, so the caller
    can splice this into a proof body without branching.
    """
    if tree is None:
        return "sorry"
    op = tree.get("op")
    if op == "leaf":
        val = tree.get("val")
        if val == "x":
            return var_name
        # Numeric leaf — annotate the type so Lean elaborates correctly.
        return f"({val} : Real)"
    if op == "eml":
        left = tree.get("left")
        right = tree.get("right")
        a = tree_to_lean(left, var_name=var_name)
        b = tree_to_lean(right, var_name=var_name)
        return f"((Real.exp ({a})) - (Real.log ({b})))"
    return "sorry"


# ──────────────────────────────────────────────────────────────────
# Source-file rendering
# ──────────────────────────────────────────────────────────────────


def _render_imports(config: EmitConfig) -> list[str]:
    out: list[str] = []
    for mod in config.machlib_imports:
        out.append(f"import {mod}")
    out.append("")
    out.append("open MachLib")
    out.append("open MachLib.Real")
    return out


def _render_witness_def(witness_lean: str,
                        theorem_name: str,
                        config: EmitConfig) -> list[str]:
    return [
        f"-- Witness term discovered by MCTS. The proof can `unfold` this",
        f"-- to expose the structural equality.",
        f"noncomputable def witness_{theorem_name} "
        f"({config.var_name} : {config.signature}) : "
        f"{config.signature} :=",
        f"  {witness_lean}",
    ]


def _proof_for_status(
    status: str,
    *,
    theorem_name: str,
    has_witness: bool,
    residual: float,
    threshold: float,
    sympy_simplification: Optional[str],
) -> tuple[list[str], str]:
    """Pick a proof body based on the prover's status.

    Returns ``(lines, kind)`` where ``kind`` is the discriminator we
    surface in the EmitResult so callers can route by proof
    strength.
    """
    if status == "proved_exact":
        # SymPy collapsed lhs - rhs to 0. MachLib has zero Mathlib
        # dependency, so `ring` / `simp` aren't available. The only
        # universal closer is `rfl` for syntactic equality. For the
        # polynomial identities that need `ring`, we fall back to
        # `sorry` with a comment so the file compiles and the human
        # can drop in the right MachLib lemma chain.
        lines = [
            f"  -- proof_exact: SymPy proved lhs - rhs = 0 "
            f"(simplification: {sympy_simplification!r})",
            "  -- MachLib has no Mathlib dependency, so `ring` is",
            "  -- unavailable. Try `rfl` for syntactic equality;",
            "  -- otherwise compose MachLib.Basic axioms manually.",
            "  first | rfl | sorry",
        ]
        return lines, "rfl_or_sorry"

    if status == "proved_witness" and has_witness:
        if residual <= threshold:
            tag = f"machine-verified (residual = {residual:.2e})"
        else:
            tag = (f"advisory only (residual = {residual:.2e} "
                   f"> threshold {threshold:.0e})")
        lines = [
            f"  -- proof_witness: MCTS found witness term; {tag}",
            f"  unfold witness_{theorem_name}",
            f"  sorry  -- TODO: prove witness equality "
            f"against MachLib axioms",
        ]
        return lines, "sorry_witness"

    if status in ("proved_certified", "proved_numerical"):
        lines = [
            f"  -- {status}: certified at residual {residual:.2e}",
            "  -- (numerical certification, not a tactic proof)",
            "  sorry  -- TODO: lift the numerical bound to a tactic proof",
        ]
        return lines, "sorry_certified"

    # Defensive fallback. We should not be called with a non-proved
    # status (the high-level emit function returns None for those),
    # but if we are, emit `sorry` with a clear note.
    lines = [
        f"  -- emitter fallback: status={status} (no tactic available)",
        "  sorry",
    ]
    return lines, "sorry_certified"


def _render_theorem(
    theorem_name: str,
    identity_str: str,
    config: EmitConfig,
    *,
    has_witness: bool,
    proof_lines: list[str],
) -> list[str]:
    """Render the theorem statement + proof body.

    The theorem statement uses the original identity string verbatim
    (modulo the ``==`` -> ``=`` swap Lean expects). We deliberately
    do NOT try to re-render the identity from the AST in v2 — that
    would require parsing arbitrary SymPy and is the v3 scope.
    """
    # SymPy `==` -> Lean `=`.
    lean_eq = identity_str.replace("==", "=")
    out = [
        f"-- Auto-generated by monogate.machlib_emitter",
        f"-- Identity: {identity_str}",
        f"-- Theorem:  {theorem_name}",
        f"theorem {theorem_name} ({config.var_name} : {config.signature}) :",
        f"    {lean_eq} := by",
    ]
    out.extend(proof_lines)
    return out


def emit_machlib_lean(
    result: Any,
    *,
    theorem_name: str,
    identity_str: Optional[str] = None,
    config: Optional[EmitConfig] = None,
) -> Optional[EmitResult]:
    """Top-level emitter.

    Args:
        result: A :class:`monogate.prover.ProofResult`. We accept ``Any``
            here so this module doesn't take an import-time dependency on
            ``monogate.prover`` (it works with any duck-typed object that
            has ``status``, ``witness_tree``, ``max_residual``,
            ``sympy_simplification``).
        theorem_name: Identifier used both as the Lean theorem name and
            as the suffix for the witness ``def``. Must be a valid Lean
            identifier — ASCII letters / digits / underscores only.
        identity_str: The original identity (e.g. ``"x*1 == x"``). When
            ``None``, falls back to ``result.identity_str``.
        config: :class:`EmitConfig` overrides; defaults are sensible.

    Returns:
        An :class:`EmitResult` for any proved status, or ``None`` if the
        proof was inconclusive / failed (the caller should not write a
        file in that case).
    """
    cfg = config or EmitConfig()
    status = getattr(result, "status", "")
    if not status.startswith("proved"):
        return None

    if identity_str is None:
        identity_str = getattr(result, "identity_str", "")

    witness_tree = getattr(result, "witness_tree", None)
    has_witness = witness_tree is not None
    residual = float(getattr(result, "max_residual", float("inf")))
    sympy_simp = getattr(result, "sympy_simplification", None)

    lines: list[str] = []
    lines.extend(_render_imports(cfg))
    lines.append("")

    if has_witness and cfg.emit_witness_def:
        witness_lean = tree_to_lean(witness_tree, var_name=cfg.var_name)
        lines.extend(_render_witness_def(witness_lean, theorem_name, cfg))
        lines.append("")

    proof_lines, kind = _proof_for_status(
        status,
        theorem_name=theorem_name,
        has_witness=has_witness,
        residual=residual,
        threshold=cfg.residual_threshold,
        sympy_simplification=sympy_simp,
    )

    lines.extend(_render_theorem(
        theorem_name,
        identity_str or "",
        cfg,
        has_witness=has_witness,
        proof_lines=proof_lines,
    ))

    code = "\n".join(lines).rstrip() + "\n"
    return EmitResult(
        code=code,
        proof_kind=kind,
        residual=residual,
        theorem_name=theorem_name,
    )
