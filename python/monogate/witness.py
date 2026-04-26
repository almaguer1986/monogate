"""monogate.witness — universality witnesses for elementary functions.

A *witness* for an expression is a finite, structured certificate
that the expression admits an EML routing tree. The witness composes
the existing eml-* substrate (`eml_cost`, `eml_discover`,
`eml_rewrite`) into a single immutable certificate object:

    >>> from monogate.witness import universality_witness
    >>> w = universality_witness("1/(1+exp(-x))")
    >>> w.profile.predicted_depth
    2
    >>> w.identified.name
    'sigmoid (canonical)'
    >>> w.verified_in_lean
    True                                # Universality.lean user-verified

When the input expression is **inside the EML class** (i.e.,
``is_pfaffian_not_eml`` is False), ``verified_in_lean`` flips to
``True`` and ``lean_url`` points at the Lean theorem
(``MonogateEML/Universality.lean`` in the public ``monogate-lean``
repository). For Pfaffian-but-not-EML primitives (Bessel, Airy,
Lambert W, hypergeometric) the flag stays False because the
universality theorem doesn't cover them.

This module was originally shipped as the standalone
``eml-witness`` package; it was folded into monogate in 2.4.0 with
``eml-witness`` archived. The standalone package's API is a strict
subset of what's exposed here — no migration required other than
updating the import path.

Optional dependency: this module is gated on the ``[witness]``
extra. ``pip install monogate[witness]`` (or ``[cli]`` /
``[jupyter]`` which pull it transitively) installs the required
``eml-cost`` / ``eml-discover`` / ``eml-rewrite`` substrate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sympy as sp

from eml_cost import analyze, fingerprint, fingerprint_axes
from eml_discover import identify
from eml_rewrite import path as walk_path


__all__ = [
    "UniversalityWitness",
    "WitnessIdentified",
    "WitnessProfile",
    "WitnessTreeNode",
    "universality_witness",
    "witness_to_dict",
    "LEAN_UNIVERSALITY_URL",
]


# Stable canonical URL for the Lean theorem the `verified_in_lean`
# flag attests to. Theorem authored 2026-04-25, user-verified in
# the VS Code lean4 extension same day per the project's Lean
# writing protocol.
LEAN_UNIVERSALITY_URL = (
    "https://github.com/almaguer1986/monogate-lean/blob/master/"
    "MonogateEML/Universality.lean"
)


# Allow-list of EML-elementary SymPy Function classes. Any
# Function call outside this set fails the strict check used
# below to gate `verified_in_lean=True` — closes a coverage gap
# where the cost detector silently treats erf / gamma / polylog
# / zeta / elliptic as depth-0 atoms even though they are
# non-elementary. Discovered via S/R-134 deep research; see
# `monogate-research/exploration/deep-research-2026-04-25-
# overnight/sr134_findings.md` for the full write-up.
_EML_ELEMENTARY_FUNCS: frozenset[type[sp.Function]] = frozenset({
    sp.exp, sp.log,
    sp.sin, sp.cos, sp.tan,
    sp.sinh, sp.cosh, sp.tanh,
    sp.asin, sp.acos, sp.atan,
    sp.asinh, sp.acosh, sp.atanh,
})


def _is_in_eml_class_strict(expr: sp.Basic) -> bool:
    """Recursively verify every Function call in ``expr`` is one of
    the EML-elementary primitives. Atoms (Symbol, Number,
    NumberSymbol like pi/E/I) are accepted; Add / Mul / Pow with
    elementary args propagate via recursion.
    """
    if isinstance(expr, sp.Function):
        if type(expr) not in _EML_ELEMENTARY_FUNCS:
            return False
        return all(_is_in_eml_class_strict(arg) for arg in expr.args)
    if expr.is_Atom:
        return True
    return all(
        _is_in_eml_class_strict(a)
        for a in expr.args
        if isinstance(a, sp.Basic)
    )


@dataclass(frozen=True)
class WitnessProfile:
    """Pfaffian profile slice of the witness.

    Fields mirror :class:`eml_cost.AnalyzeResult` but are flattened
    for JSON serialisation.
    """

    pfaffian_r: int
    max_path_r: int
    eml_depth: int
    structural_overhead: int
    predicted_depth: int
    is_pfaffian_not_eml: bool
    c_osc: int
    c_composite: int
    delta_fused: int
    fingerprint: str
    axes: str


@dataclass(frozen=True)
class WitnessIdentified:
    """Best registry match for the input expression."""

    name: str
    confidence: str
    domain: str
    citation: str
    description: str


@dataclass(frozen=True)
class WitnessTreeNode:
    """A single step in the canonical-equivalent rewrite path."""

    pattern_name: str
    expression_str: str
    cost: int


@dataclass(frozen=True)
class UniversalityWitness:
    """Complete witness object — see module docstring.

    Use :func:`witness_to_dict` to serialise to a JSON-safe dict.

    ``canonical_path`` is a tuple (not a list) so the dataclass is
    *deeply* immutable — ``frozen=True`` only protects against
    reassignment of the field itself; a list field would still be
    mutable in place.
    """

    input_expr_str: str
    profile: WitnessProfile
    identified: WitnessIdentified | None
    canonical_path: tuple[WitnessTreeNode, ...] = field(default_factory=tuple)
    savings: int = 0
    verified_in_lean: bool = False
    lean_url: str | None = None


def universality_witness(
    expr: sp.Basic | str,
    *,
    walk_canonical: bool = True,
    canonical_target: sp.Basic | None = None,
) -> UniversalityWitness:
    """Build a universality witness for ``expr``.

    Parameters
    ----------
    expr:
        SymPy expression or sympify-able string.
    walk_canonical:
        When True (default), attempt to reduce ``expr`` to a
        lower-cost equivalent via :func:`eml_rewrite.path`.
    canonical_target:
        Optional explicit target expression to walk toward.

    Returns
    -------
    UniversalityWitness
        Frozen dataclass with profile, identification, and path.
        ``verified_in_lean`` is True when the input is inside the
        EML class (``is_pfaffian_not_eml=False``) and the Lean
        theorem is user-verified (which it is as of 2026-04-25).
    """
    if isinstance(expr, str):
        try:
            parsed: sp.Basic = sp.sympify(expr)
        except Exception as exc:
            raise ValueError(f"Could not parse expression: {expr!r}") from exc
    elif isinstance(expr, sp.Basic):
        parsed = expr
    else:
        raise TypeError(
            f"universality_witness expects str or sp.Basic, got {type(expr).__name__}"
        )

    a = analyze(parsed)
    fp = fingerprint(parsed)
    axes = fingerprint_axes(parsed)

    profile = WitnessProfile(
        pfaffian_r=a.pfaffian_r,
        max_path_r=a.max_path_r,
        eml_depth=a.eml_depth,
        structural_overhead=a.structural_overhead,
        predicted_depth=a.predicted_depth,
        is_pfaffian_not_eml=a.is_pfaffian_not_eml,
        c_osc=a.corrections.c_osc,
        c_composite=a.corrections.c_composite,
        delta_fused=a.corrections.delta_fused,
        fingerprint=fp,
        axes=axes,
    )

    matches = identify(parsed, max_results=1)
    identified: WitnessIdentified | None = None
    if matches:
        m = matches[0]
        identified = WitnessIdentified(
            name=m.formula.name,
            confidence=m.confidence,
            domain=getattr(m.formula, "domain", "unknown"),
            citation=getattr(m.formula, "citation", ""),
            description=getattr(m.formula, "description", ""),
        )

    path_steps: list[WitnessTreeNode] = []
    savings = 0
    if walk_canonical:
        target: sp.Basic | None = canonical_target
        if target is None:
            try:
                from eml_rewrite import best as _best
                better = _best(parsed)
                if better != parsed:
                    target = better
            except (ImportError, AttributeError, RecursionError):
                target = None
        if target is not None and target != parsed:
            try:
                steps = walk_path(parsed, target)
            except (ValueError, RecursionError, AttributeError):
                steps = None
            if steps is not None:
                for s in steps:
                    path_steps.append(WitnessTreeNode(
                        pattern_name=s.pattern_name,
                        expression_str=str(s.expression),
                        cost=s.cost,
                    ))
                if len(steps) >= 2:
                    savings = steps[0].cost - steps[-1].cost

    # Lean coverage: theorem covers EML-elementary functions only.
    # Two-step gate — (a) the cost detector must NOT flag the
    # expression as Pfaffian-but-not-EML (catches Bessel, Airy,
    # LambertW, hypergeometric); (b) the strict allow-list check
    # must pass (catches erf, gamma, polylog, zeta, elliptic, ...
    # which the detector silently treats as depth-0 atoms — the
    # 0.2.1 / 2.4.3 hotfix).
    is_within_eml_class = (
        (not profile.is_pfaffian_not_eml)
        and _is_in_eml_class_strict(parsed)
    )

    return UniversalityWitness(
        input_expr_str=str(parsed),
        profile=profile,
        identified=identified,
        canonical_path=tuple(path_steps),
        savings=savings,
        verified_in_lean=is_within_eml_class,
        lean_url=LEAN_UNIVERSALITY_URL if is_within_eml_class else None,
    )


def witness_to_dict(w: UniversalityWitness) -> dict[str, Any]:
    """Serialise a :class:`UniversalityWitness` to a JSON-safe dict."""
    return {
        "input_expr": w.input_expr_str,
        "profile": {
            "pfaffian_r": w.profile.pfaffian_r,
            "max_path_r": w.profile.max_path_r,
            "eml_depth": w.profile.eml_depth,
            "structural_overhead": w.profile.structural_overhead,
            "predicted_depth": w.profile.predicted_depth,
            "is_pfaffian_not_eml": w.profile.is_pfaffian_not_eml,
            "corrections": {
                "c_osc": w.profile.c_osc,
                "c_composite": w.profile.c_composite,
                "delta_fused": w.profile.delta_fused,
            },
            "fingerprint": w.profile.fingerprint,
            "axes": w.profile.axes,
        },
        "identified": (
            None if w.identified is None
            else {
                "name": w.identified.name,
                "confidence": w.identified.confidence,
                "domain": w.identified.domain,
                "citation": w.identified.citation,
                "description": w.identified.description,
            }
        ),
        "canonical_path": [
            {
                "pattern_name": n.pattern_name,
                "expression": n.expression_str,
                "cost": n.cost,
            }
            for n in w.canonical_path
        ],
        "savings": w.savings,
        "verified_in_lean": w.verified_in_lean,
        "lean_url": w.lean_url,
    }
