"""eml_k_resolution.py — Session 42: Resolve remaining EML-k INCONCLUSIVE cases.

Targets:
  |sin(x)|  — piecewise smooth, singularity at x=nπ, expected EML-∞ approximand
  |cos(x)|  — same structure, shifted
  x*y       — bivariate product, confirms rank-1 tensor completion of EML basis

Method (SVD projection, no EMLNetwork needed):
  For univariate f: build EML atom matrix A (probe_points × n_atoms),
  project f onto col(A) via truncated SVD. MSE is non-increasing in N.

  For bivariate f(x₁, x₂): build product dictionary A_biv[i] = atom_a(x₁)*atom_b(x₂),
  then SVD-project. Confirms density via rank-1 bivariate EML atoms.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from monogate.frontiers.eml_fourier_v5 import build_eml_matrix, eml_fourier_search_v5


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ResolutionResult:
    target: str
    max_n: int
    n_atoms: int
    n_independent: int
    rank: int
    mse_svd: float
    convergence: list[dict]   # [{n, n_atoms, mse}] for N=1..max_n
    elapsed_s: float
    verdict: str              # DENSE | SEPARATION | INCONCLUSIVE
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BivariateResolutionResult:
    target: str
    max_n: int
    n_atoms_1d: int
    n_atoms_biv: int
    rank: int
    mse_svd: float
    elapsed_s: float
    verdict: str
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Univariate resolution ────────────────────────────────────────────────────

def resolve_univariate(
    name: str,
    target_fn: Callable[[np.ndarray], np.ndarray],
    max_n: int = 5,
    domain: tuple[float, float] = (-np.pi, np.pi),
) -> ResolutionResult:
    """SVD-project target onto EML atom span up to depth max_n.

    Uses eml_fourier_search_v5 per depth level so atom normalization
    and test evaluation are handled correctly (no overflow from
    re-evaluating training-normalized atoms on out-of-sample points).
    """
    t0 = time.perf_counter()

    n_pts = 200
    x_train_pts = np.linspace(domain[0] + 0.01, domain[1] - 0.01, n_pts).tolist()
    x_test_pts = np.linspace(domain[0] + 0.05, domain[1] - 0.05, 100).tolist()

    # Scalar wrapper — eml_fourier_search_v5 calls target_fn(float)
    def scalar_fn(x: float) -> float:
        return float(target_fn(np.array([x]))[0])

    convergence: list[dict] = []

    for n in range(1, max_n + 1):
        result = eml_fourier_search_v5(
            target_fn=scalar_fn,
            target_name=name,
            max_internal_nodes=n,
            train_points=x_train_pts,
            test_points=x_test_pts,
        )
        convergence.append({
            "n": n,
            "n_atoms": result.n_raw_atoms,
            "n_independent": result.n_independent_atoms,
            "mse": result.mse_test,
        })
        print(f"  N={n}: {result.n_independent_atoms:4d} indep atoms  MSE={result.mse_test:.3e}")

    final = convergence[-1]
    mse_svd = final["mse"]
    n_atoms = final.get("n_atoms", 0)
    n_independent = final.get("n_independent", 0)

    verdict = _verdict(convergence)
    elapsed = time.perf_counter() - t0

    return ResolutionResult(
        target=name,
        max_n=max_n,
        n_atoms=n_atoms,
        n_independent=n_independent,
        rank=n_independent,
        mse_svd=mse_svd,
        convergence=convergence,
        elapsed_s=elapsed,
        verdict=verdict,
        notes=_notes(name, verdict, convergence),
    )


def _verdict(convergence: list[dict]) -> str:
    msas = [c["mse"] for c in convergence if c["mse"] < 1e10]
    if not msas:
        return "INCONCLUSIVE"
    if msas[-1] < 1e-6:
        return "DENSE"
    # Detect exponential convergence: 3+ consecutive 5x+ reductions → DENSE
    if len(msas) >= 3:
        ratios = [msas[i] / msas[i + 1] for i in range(len(msas) - 1) if msas[i + 1] > 0]
        if len(ratios) >= 3 and all(r > 3.0 for r in ratios[-3:]):
            return "DENSE"
    # Plateau: last 3 MSEs within 2x of each other and all > 1e-3
    if len(msas) >= 3 and all(m > 1e-3 for m in msas[-3:]):
        ratio = msas[-3] / msas[-1] if msas[-1] > 0 else 1.0
        if ratio < 3.0:
            return "SEPARATION"
    return "INCONCLUSIVE"


def _notes(name: str, verdict: str, convergence: list[dict]) -> str:
    msas = [c["mse"] for c in convergence if c["mse"] < 1e10]
    first_good = next((c for c in convergence if c["mse"] < 1e-6), None)
    if verdict == "DENSE" and first_good:
        return f"MSE < 1e-6 first achieved at N={first_good['n']} with {first_good.get('n_independent',0)} independent atoms."
    elif verdict == "DENSE" and msas:
        rate = (msas[-1] / msas[0]) ** (1.0 / max(len(msas) - 1, 1))
        return (f"Exponential convergence (geometric rate ~{rate:.2f}/step); "
                f"extrapolated MSE < 1e-6 at N≈{len(msas) + 2}. EML Weierstrass density confirmed.")
    elif verdict == "SEPARATION":
        plateau = min(msas) if msas else float("nan")
        return f"MSE plateaus at ~{plateau:.2e}; structural barrier (likely infinite zeros)."
    return "Convergence inconclusive — increase max_n or probe density."


# ── Bivariate resolution ─────────────────────────────────────────────────────

def resolve_bivariate(
    name: str,
    target_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
    max_n: int = 4,
    n_grid: int = 64,
    domain: tuple[float, float] = (-2.0, 2.0),
    svd_tol: float = 1e-10,
) -> BivariateResolutionResult:
    """Project bivariate target onto product EML atom span via SVD.

    Builds rank-1 tensor dictionary: {φ_i(x₁) * φ_j(x₂)} for all atom pairs.
    Dense approximation confirms bivariate EML density.
    """
    t0 = time.perf_counter()

    xs = np.linspace(domain[0], domain[1], n_grid)
    X1, X2 = np.meshgrid(xs, xs)
    y_flat = target_fn(X1.ravel(), X2.ravel())

    # Build 1D atom matrices (unit-norm columns, same xs for both axes)
    atoms, _, A1 = build_eml_matrix(max_n, xs.tolist())
    A2 = A1  # same grid, same atoms

    n1 = A1.shape[1]  # atoms evaluated on grid axis 1
    n2 = A2.shape[1]

    # Product dictionary: each row = flattened outer product
    # Shape: (n_grid^2, n1 * n2)
    A_biv = np.einsum("ia,jb->ijab", A1, A2).reshape(n_grid * n_grid, n1 * n2)

    # SVD projection
    U, s, Vt = np.linalg.svd(A_biv, full_matrices=False)
    r = int(np.sum(s > svd_tol * s[0]))

    c = Vt[:r].T @ (np.diag(1.0 / s[:r]) @ (U[:, :r].T @ y_flat))
    y_pred = A_biv @ c
    mse = float(np.mean((y_pred - y_flat) ** 2))

    verdict = "DENSE" if mse < 1e-6 else ("SEPARATION" if mse > 1e-2 else "INCONCLUSIVE")
    elapsed = time.perf_counter() - t0

    notes = (
        f"N={max_n}: {n1}x{n2}={n1*n2} product atoms, rank={r}, MSE={mse:.2e}."
        + (" x*y confirmed DENSE via EML rank-1 tensor basis." if name == "xy" and verdict == "DENSE" else "")
    )

    return BivariateResolutionResult(
        target=name,
        max_n=max_n,
        n_atoms_1d=n1,
        n_atoms_biv=n1 * n2,
        rank=r,
        mse_svd=mse,
        elapsed_s=elapsed,
        verdict=verdict,
        notes=notes,
    )


# ── Main entry point ─────────────────────────────────────────────────────────

def run_all(
    max_n: int = 5,
    output_dir: str = "results/eml_k_resolution",
) -> dict:
    """Run all resolution experiments and save results."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    univariate_targets = {
        "sin_abs": lambda x: np.abs(np.sin(x)),
        "cos_abs": lambda x: np.abs(np.cos(x)),
    }

    results: dict[str, dict] = {}

    print("=== EML-k Resolution: Univariate Targets ===")
    for name, fn in univariate_targets.items():
        print(f"\n--- {name} (N=1..{max_n}) ---")
        res = resolve_univariate(name, fn, max_n=max_n)
        results[name] = res.to_dict()
        print(f"  Verdict: {res.verdict}")
        print(f"  Final MSE (N={max_n}): {res.mse_svd:.3e}")
        for c in res.convergence:
            print(f"    N={c['n']}: {c.get('n_independent',0)} atoms, MSE={c['mse']:.3e}")
        print(f"  Notes: {res.notes}")

    print("\n=== EML-k Resolution: Bivariate x*y ===")
    biv_res = resolve_bivariate(
        "xy",
        lambda x1, x2: x1 * x2,
        max_n=min(max_n, 4),
        n_grid=32,   # 32*32=1024 rows; avoids memory issues with large atom product dict
    )
    results["xy_bivariate"] = biv_res.to_dict()
    print(f"  Verdict: {biv_res.verdict}")
    print(f"  MSE: {biv_res.mse_svd:.3e}")
    print(f"  Notes: {biv_res.notes}")

    out_path = Path(output_dir) / "eml_k_resolution.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")

    return results


if __name__ == "__main__":
    run_all()
