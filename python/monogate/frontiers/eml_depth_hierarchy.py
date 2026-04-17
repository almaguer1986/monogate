"""EML-k Complexity Hierarchy — formal depth classes for function approximation.

Defines the EML-k complexity class:

  EML-k = {f ∈ C[a,b] | ∃ finitely many EML trees T₁,...,Tₘ (depth ≤ k)
           and coefficients c₁,...,cₘ s.t. ||f - Σcᵢ·Tᵢ||₂ < ε}

This is the continuous analogue of Boolean circuit complexity classes, but
for smooth functions and algebraic gates.

Grammar hierarchy connection (grammar_hierarchy.py G0–G5):
  G1 (EML only, {1,x}) corresponds to depth-k atoms in this module.
  G2 (EML+DEML) extends the atom set with deml(x,y) = exp(-x) - ln(y).
  G3 (EML+DEML+EXL) adds exl(x,y) = exp(x)·ln(y).

Key findings (Session 38):
  - EML is DENSE for sin(x), cos(x), sinh(x), erf(x), lgamma(x) (5/8 tested)
  - Universal N=3 singularity: most smooth functions show their largest improvement at N=3
  - sinh(x) shows 10B× improvement at N=3 (most EML-natural smooth function)
  - |sin(x)| and j0(x) (non-smooth/multi-oscillation) resist easy classification
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from monogate.frontiers.eml_fourier_v5 import eml_fourier_search_v5

_DEFAULT_TRAIN = list(np.linspace(0.05, 6.28, 300))
_DEFAULT_TEST = list(np.linspace(0.1, 6.27, 150))


@dataclass
class EMLComplexityResult:
    function_name: str
    domain: tuple[float, float]
    floor_by_N: dict[int, float] = field(default_factory=dict)
    rank_by_N: dict[int, int] = field(default_factory=dict)
    min_depth_1e6: int = -1   # minimum N where floor < 1e-6 (-1 = not reached)
    min_depth_1e10: int = -1  # minimum N where floor < 1e-10 (-1 = not reached)
    n3_jump_factor: float = float("nan")  # floor(N=2) / floor(N=3)
    verdict: str = "INCONCLUSIVE"
    mean_improvement_ratio: float = float("nan")  # mean floor(N-1)/floor(N)
    errors: dict[int, str] = field(default_factory=dict)

    def complexity_class(self, eps: float = 1e-6) -> int:
        """Minimum N achieving floor < eps, or -1 if not reached."""
        for n in sorted(self.floor_by_N):
            if self.floor_by_N[n] < eps:
                return n
        return -1

    def __str__(self) -> str:
        lines = [f"EMLComplexityResult({self.function_name})"]
        lines.append(f"  domain: {self.domain}")
        lines.append(f"  verdict: {self.verdict}")
        for n, mse in sorted(self.floor_by_N.items()):
            lines.append(f"  N={n}: mse={mse:.4e}  rank={self.rank_by_N.get(n, '?')}")
        if math.isfinite(self.n3_jump_factor):
            lines.append(f"  N=3 jump: {self.n3_jump_factor:.1f}×")
        lines.append(f"  min depth for 1e-6: {self.min_depth_1e6}")
        lines.append(f"  min depth for 1e-10: {self.min_depth_1e10}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "function_name": self.function_name,
            "domain": list(self.domain),
            "floor_by_N": {str(k): v for k, v in self.floor_by_N.items()},
            "rank_by_N": {str(k): v for k, v in self.rank_by_N.items()},
            "min_depth_1e6": self.min_depth_1e6,
            "min_depth_1e10": self.min_depth_1e10,
            "n3_jump_factor": self.n3_jump_factor if math.isfinite(self.n3_jump_factor) else None,
            "verdict": self.verdict,
            "mean_improvement_ratio": (
                self.mean_improvement_ratio if math.isfinite(self.mean_improvement_ratio) else None
            ),
        }


def eml_complexity_class(
    target_fn: Callable[[float], float],
    target_name: str = "f",
    max_N: int = 5,
    train_points: list[float] | None = None,
    test_points: list[float] | None = None,
) -> EMLComplexityResult:
    """Compute the EML complexity class of a function via SVD floor sweep.

    Runs eml_fourier_search_v5 for N=1..max_N and classifies the function as:
      DENSE       — floor decays to zero (supported by monotone decay to < 1e-6 by N≤max_N)
      LIKELY_DENSE — consistent decay but not yet at 1e-6
      SEPARATION  — floor plateaued above 1e-4
      INCONCLUSIVE — mixed signal or numerical issues

    Returns:
        EMLComplexityResult with floor_by_N, rank_by_N, n3_jump_factor, verdict.
    """
    if train_points is None:
        train_points = _DEFAULT_TRAIN
    if test_points is None:
        test_points = _DEFAULT_TEST

    domain = (float(min(train_points)), float(max(train_points)))
    result = EMLComplexityResult(function_name=target_name, domain=domain)

    for n in range(1, max_N + 1):
        try:
            r = eml_fourier_search_v5(
                target_fn=target_fn,
                target_name=target_name,
                max_internal_nodes=n,
                train_points=train_points,
                test_points=test_points,
            )
            result.floor_by_N[n] = r.mse_test
            result.rank_by_N[n] = r.n_independent_atoms
        except Exception as exc:
            result.errors[n] = str(exc)

    # Derived metrics
    valid_N = sorted(k for k in result.floor_by_N if math.isfinite(result.floor_by_N[k]))

    if valid_N:
        mses = [result.floor_by_N[n] for n in valid_N]

        # min depth thresholds
        for n in valid_N:
            m = result.floor_by_N[n]
            if m < 1e-6 and result.min_depth_1e6 < 0:
                result.min_depth_1e6 = n
            if m < 1e-10 and result.min_depth_1e10 < 0:
                result.min_depth_1e10 = n

        # N=3 jump factor
        if 2 in result.floor_by_N and 3 in result.floor_by_N:
            m2 = result.floor_by_N[2]
            m3 = result.floor_by_N[3]
            if math.isfinite(m2) and math.isfinite(m3) and m3 > 0:
                result.n3_jump_factor = m2 / m3

        # Mean improvement ratio per level
        if len(mses) >= 2:
            ratios = [mses[i] / mses[i-1] for i in range(1, len(mses))
                      if mses[i-1] > 1e-30 and math.isfinite(mses[i])]
            if ratios:
                result.mean_improvement_ratio = float(1.0 / np.mean(ratios))

        # Verdict
        is_monotone = all(
            mses[i] <= mses[i-1] * 1.1
            for i in range(1, len(mses))
        )
        last_mse = mses[-1]

        if not is_monotone:
            # Check if it's just machine-precision noise
            if last_mse < 1e-12 and min(mses) < 1e-12:
                result.verdict = "DENSE"
            else:
                result.verdict = "INCONCLUSIVE"
        elif last_mse < 1e-6:
            result.verdict = "DENSE"
        elif result.mean_improvement_ratio > 2.0:
            result.verdict = "LIKELY_DENSE"
        elif len(ratios if 'ratios' in dir() else []) >= 2 and ratios[-1] > 0.85:
            result.verdict = "SEPARATION"
        else:
            result.verdict = "INCONCLUSIVE"

    return result


# Precomputed results for known functions (from Session 38 survey)
KNOWN_COMPLEXITY: dict[str, dict] = {
    "sin(x)":    {"min_depth_1e6": 3, "n3_jump": 137220, "verdict": "DENSE"},
    "cos(x)":    {"min_depth_1e6": 3, "n3_jump": 88475, "verdict": "DENSE"},
    "sinh(x)":   {"min_depth_1e6": 2, "n3_jump": 10_029_085_666, "verdict": "DENSE"},
    "erf(x)":    {"min_depth_1e6": 3, "n3_jump": 45_557_389, "verdict": "DENSE"},
    "lgamma(x)": {"min_depth_1e6": 2, "n3_jump": 14_981_633, "verdict": "DENSE"},
    "x^(1/3)":   {"min_depth_1e6": 3, "n3_jump": 269_825_301, "verdict": "LIKELY_DENSE"},
    "|sin(x)|":  {"min_depth_1e6": -1, "n3_jump": 22, "verdict": "INCONCLUSIVE"},
    "j0(x)":     {"min_depth_1e6": -1, "n3_jump": 0.2, "verdict": "INCONCLUSIVE"},
}
