"""
monogate.frontiers.law_complexity
===================================
Physics Law Complexity Census — measures the EML complexity of fundamental
physical laws and compares them to random algebraic controls.

**EML complexity** is operationalised as the minimum number of MCTS simulations
(measured as best MSE at depth 1 / 3 / 5 nodes) needed to approximate a law's
functional form.  Laws that are "native" to the EML basis (those whose functional
form is directly `exp(·)` or combinations of one EML gate) achieve near-zero MSE
at depth 1.  Laws that require many nested operations (power laws, composite
expressions) achieve lower MSE only at higher depths.

Three levels of analysis
------------------------
1. **Identity census** — laws expressed as ``lhs == rhs``, proved by
   :class:`~monogate.prover.EMLProverV2`.  Records proof tier and witness nodes.
2. **Functional census** — laws expressed as 1-variable functions.  Records
   the best MSE achievable by MCTS at each EML depth.
3. **Rediscovery benchmark** — fit EMLRegressor to synthetic noisy data and
   check whether the discovered formula matches the ground truth.

Usage::

    cd python
    python -m monogate.frontiers.law_complexity
"""

from __future__ import annotations

import math
import random
import time
from typing import Any, Callable

import numpy as np


# ── Law catalogs ──────────────────────────────────────────────────────────────

# Laws expressed as mathematical identities (lhs == rhs)
IDENTITY_LAWS: list[dict] = [
    # ── Thermodynamics / Statistical Mechanics ────────────────────────────────
    {
        "name":        "Boltzmann entropy (additive)",
        "category":    "thermodynamics",
        "expression":  "exp(x) * exp(y) == exp(x + y)",
        "description": "Partition function factorisation",
    },
    {
        "name":        "Free energy relation",
        "category":    "thermodynamics",
        "expression":  "exp(x) / exp(y) == exp(x - y)",
        "description": "Ratio of Boltzmann factors",
    },
    {
        "name":        "Entropy log identity",
        "category":    "thermodynamics",
        "expression":  "log(exp(x)) == x",
        "description": "ln(e^x) = x",
    },
    {
        "name":        "Gibbs factor",
        "category":    "thermodynamics",
        "expression":  "exp(log(x)) == x",
        "description": "e^(ln x) = x  (x > 0)",
    },
    # ── Classical Mechanics ───────────────────────────────────────────────────
    {
        "name":        "Double-angle energy",
        "category":    "mechanics",
        "expression":  "2*sin(x)*cos(x) == sin(2*x)",
        "description": "Oscillator energy double-angle form",
    },
    {
        "name":        "Pythagorean (energy partition)",
        "category":    "mechanics",
        "expression":  "sin(x)**2 + cos(x)**2 == 1",
        "description": "sin²+cos²=1 — normalisation of harmonic oscillator states",
    },
    {
        "name":        "Hyperbolic identity (rapidity)",
        "category":    "relativity",
        "expression":  "cosh(x)**2 - sinh(x)**2 == 1",
        "description": "Rapidity addition in special relativity",
    },
    {
        "name":        "Tanh via sinh/cosh",
        "category":    "relativity",
        "expression":  "tanh(x) == sinh(x) / cosh(x)",
        "description": "Velocity–rapidity relation tanh(φ)=v/c",
    },
    # ── Electromagnetism / Optics ─────────────────────────────────────────────
    {
        "name":        "Phasor exponential",
        "category":    "electromagnetism",
        "expression":  "exp(x + y) == exp(x) * exp(y)",
        "description": "Superposition of EM fields in phasor notation",
    },
    {
        "name":        "RC discharge identity",
        "category":    "electromagnetism",
        "expression":  "exp(-x) * exp(x) == 1",
        "description": "Charge conservation in RC circuit: V(t)·V(-t) = V₀²",
    },
    # ── Quantum Mechanics ─────────────────────────────────────────────────────
    {
        "name":        "Norm of Gaussian wavefunction",
        "category":    "quantum",
        "expression":  "exp(x)**2 == exp(2*x)",
        "description": "|ψ|² = exp(2·Re(x)) for real Gaussian wavefunction",
    },
    {
        "name":        "Commutator-free evolution",
        "category":    "quantum",
        "expression":  "exp(2*x) == exp(x)**2",
        "description": "exp(2H) = [exp(H)]² when [H,H]=0",
    },
    # ── Statistical Mechanics ─────────────────────────────────────────────────
    {
        "name":        "Partition function ratio",
        "category":    "statistical",
        "expression":  "exp(x - y) == exp(x) / exp(y)",
        "description": "Z₁/Z₂ = exp(ΔF/kT)",
    },
    {
        "name":        "Boltzmann detailed balance",
        "category":    "statistical",
        "expression":  "exp(x) * exp(-x) == 1",
        "description": "Detailed balance condition: forward/backward rate ratio",
    },
    # ── Information Theory ────────────────────────────────────────────────────
    {
        "name":        "Cross-entropy bound",
        "category":    "information",
        "expression":  "log(exp(x) * exp(y)) == x + y",
        "description": "Additivity of log-probabilities",
    },
]


# Laws expressed as 1-variable functions (for EML approximation census)
FUNCTIONAL_LAWS: list[dict] = [
    # ── Exponential / Thermodynamic (EML-native candidates) ──────────────────
    {
        "name":     "Boltzmann weight",
        "category": "thermodynamics",
        "fn":       lambda x: math.exp(x),
        "domain":   (0.0, 3.0),
        "description": "Z = exp(-E/kT), E/kT = -x",
        "expected": "1-node EML (native: eml(x, 1))",
    },
    {
        "name":     "Exponential decay",
        "category": "statistical",
        "fn":       lambda x: math.exp(-x),
        "domain":   (0.1, 3.0),
        "description": "Radioactive decay N(t)=N₀exp(-λt), x=λt",
        "expected": "3-5 nodes (requires building -x)",
    },
    {
        "name":     "Arrhenius rate",
        "category": "chemistry",
        "fn":       lambda x: math.exp(-1.0 / x),
        "domain":   (0.5, 5.0),
        "description": "k=A·exp(-Ea/RT), x=RT/Ea",
        "expected": "3-5 nodes (requires 1/x then exp)",
    },
    {
        "name":     "RC discharge",
        "category": "electromagnetism",
        "fn":       lambda x: 1.0 - math.exp(-x),
        "domain":   (0.0, 4.0),
        "description": "V(t)=V₀(1-exp(-t/RC)), x=t/RC",
        "expected": "3-5 nodes (1 - exp(-x))",
    },
    {
        "name":     "Planck / Bose-Einstein",
        "category": "quantum",
        "fn":       lambda x: 1.0 / (math.exp(x) - 1.0),
        "domain":   (0.5, 4.0),
        "description": "⟨n⟩=1/(exp(hν/kT)-1), x=hν/kT",
        "expected": "3-5 nodes",
    },
    {
        "name":     "Fermi-Dirac",
        "category": "quantum",
        "fn":       lambda x: 1.0 / (math.exp(x) + 1.0),
        "domain":   (-3.0, 3.0),
        "description": "f(E)=1/(exp((E-μ)/kT)+1)",
        "expected": "3-5 nodes",
    },
    {
        "name":     "Maxwell-Boltzmann speed",
        "category": "statistical",
        "fn":       lambda x: x * x * math.exp(-x * x / 2.0),
        "domain":   (0.0, 4.0),
        "description": "f(v)∝v²·exp(-mv²/2kT), x=v/v_th",
        "expected": "5-7 nodes",
    },
    {
        "name":     "Entropy (information)",
        "category": "information",
        "fn":       lambda x: -x * math.log(x) if x > 0 else 0.0,
        "domain":   (0.01, 1.0),
        "description": "H=-p·ln(p) contribution per state",
        "expected": "3-5 nodes",
    },
    # ── Power laws (non-EML-native) ───────────────────────────────────────────
    {
        "name":     "Kepler 3rd law",
        "category": "mechanics",
        "fn":       lambda x: x ** 1.5,
        "domain":   (0.5, 3.0),
        "description": "T ∝ a^(3/2)",
        "expected": "5-7 nodes (power law needs exp·log composition)",
    },
    {
        "name":     "Newtonian gravity",
        "category": "mechanics",
        "fn":       lambda x: 1.0 / (x * x),
        "domain":   (0.5, 3.0),
        "description": "F ∝ 1/r²",
        "expected": "5-7 nodes",
    },
    {
        "name":     "Kinetic energy",
        "category": "mechanics",
        "fn":       lambda x: 0.5 * x * x,
        "domain":   (0.0, 3.0),
        "description": "KE = ½mv², x=v",
        "expected": "5-7 nodes (polynomial)",
    },
    {
        "name":     "Wien's law",
        "category": "thermodynamics",
        "fn":       lambda x: 1.0 / x,
        "domain":   (0.5, 5.0),
        "description": "λ_max·T = b → λ_max = b/T",
        "expected": "3-5 nodes (1/x = exp(-ln(x)))",
    },
    {
        "name":     "Stefan-Boltzmann",
        "category": "thermodynamics",
        "fn":       lambda x: x ** 4,
        "domain":   (0.5, 2.0),
        "description": "P = σT⁴",
        "expected": "5-7 nodes",
    },
    {
        "name":     "Lorentz factor",
        "category": "relativity",
        "fn":       lambda x: 1.0 / math.sqrt(1.0 - x * x),
        "domain":   (0.0, 0.9),
        "description": "γ = 1/√(1-β²), x=v/c",
        "expected": "5-7 nodes",
    },
    {
        "name":     "Gaussian wavefunction",
        "category": "quantum",
        "fn":       lambda x: math.exp(-x * x),
        "domain":   (-2.0, 2.0),
        "description": "ψ(x) ∝ exp(-x²/2σ²), ground state harmonic oscillator",
        "expected": "3-5 nodes",
    },
]


# ── Core complexity measurement ───────────────────────────────────────────────

def measure_eml_profile(
    fn:            Callable[[float], float],
    domain:        tuple[float, float],
    depths:        tuple[int, ...] = (2, 4, 6),
    n_simulations: int = 1500,
    n_probe:       int = 80,
    seed:          int = 42,
) -> dict:
    """Measure best MSE achievable at each EML depth for *fn* on *domain*.

    depth semantics in mcts_search:
      depth=1 → leaf-only tree (no EML gates); just constants or x
      depth=2 → 1 EML gate with leaf children  (1-node EML)
      depth=4 → up to 3 nested EML gates
      depth=6 → up to 5 nested EML gates

    Returns
    -------
    dict with keys ``depth_<d>`` → ``{"mse": float, "formula": str}``.
    Also includes ``"eml_native"`` (True if depth=2 achieves MSE < 1e-6),
    ``"min_effective_depth"`` (smallest depth with MSE < 0.05), and
    ``"elapsed_s"``.
    """
    from monogate.search.mcts import mcts_search

    lo, hi = domain
    probe_points = [lo + (hi - lo) * i / (n_probe - 1) for i in range(n_probe)]

    # Guard: filter out non-finite targets
    probe_y = []
    valid_probes = []
    for x in probe_points:
        try:
            y = fn(x)
            if math.isfinite(y):
                probe_y.append(y)
                valid_probes.append(x)
        except Exception:
            pass

    if len(valid_probes) < 10:
        return {"error": "insufficient valid probe points"}

    results = {}
    t0 = time.perf_counter()

    for depth in depths:
        try:
            r = mcts_search(
                target_fn=fn,
                probe_points=valid_probes,
                depth=depth,
                n_simulations=n_simulations,
                seed=seed,
                objective="mse",
            )
            results[f"depth_{depth}"] = {
                "mse":     r.best_mse,
                "formula": r.best_formula or "",
            }
        except Exception as exc:
            results[f"depth_{depth}"] = {"mse": float("inf"), "formula": "", "error": str(exc)}

    elapsed = time.perf_counter() - t0

    # Derived summary
    min_depth = min(depths)
    mse_min_depth = results.get(f"depth_{min_depth}", {}).get("mse", float("inf"))
    min_eff_depth = None
    for d in depths:
        if results.get(f"depth_{d}", {}).get("mse", float("inf")) < 0.05:
            min_eff_depth = d
            break

    # eml_native: achieves near-zero MSE at minimum depth (depth=2 = 1 EML gate)
    results["eml_native"]          = mse_min_depth < 1e-6
    results["min_effective_depth"] = min_eff_depth
    results["elapsed_s"]           = elapsed

    return results


def census_functional(
    n_simulations: int = 1500,
    verbose:       bool = True,
) -> list[dict]:
    """Run the functional EML census over all FUNCTIONAL_LAWS.

    Returns a list of result dicts, one per law.
    """
    rows = []
    n = len(FUNCTIONAL_LAWS)
    for i, law in enumerate(FUNCTIONAL_LAWS):
        if verbose:
            print(f"  [{i+1}/{n}] {law['name']:40s} ...", end="", flush=True)
        t0 = time.perf_counter()
        profile = measure_eml_profile(
            law["fn"], law["domain"],
            depths=(2, 4, 6),
            n_simulations=n_simulations,
        )
        elapsed = time.perf_counter() - t0

        row = {
            "name":          law["name"],
            "category":      law["category"],
            "description":   law["description"],
            "expected":      law.get("expected", ""),
            **profile,
        }
        rows.append(row)

        if verbose:
            d2 = profile.get("depth_2", {}).get("mse", 999)
            d4 = profile.get("depth_4", {}).get("mse", 999)
            d6 = profile.get("depth_6", {}).get("mse", 999)
            native = "NATIVE" if profile.get("eml_native") else f"eff_d={profile.get('min_effective_depth', '?')}"
            print(f" d2={d2:.3f} d4={d4:.3f} d6={d6:.3f}  [{native}] ({elapsed:.1f}s)")

    return rows


def census_identities(verbose: bool = True) -> list[dict]:
    """Prove each identity law with EMLProverV2.

    Returns a list of result dicts with proof tier, elapsed_s, node_count.
    """
    from monogate.prover import EMLProverV2

    prover = EMLProverV2(enable_learning=False)
    rows = []
    n = len(IDENTITY_LAWS)
    for i, law in enumerate(IDENTITY_LAWS):
        if verbose:
            print(f"  [{i+1}/{n}] {law['name']:40s} ...", end="", flush=True)

        r = prover.prove(law["expression"])
        row = {
            "name":        law["name"],
            "category":    law["category"],
            "expression":  law["expression"],
            "status":      r.status,
            "tier":        _status_to_tier(r.status),
            "confidence":  r.confidence,
            "elapsed_s":   r.elapsed_s,
            "node_count":  r.node_count,
            "lhs_formula": r.lhs_formula,
        }
        rows.append(row)

        if verbose:
            symbol = "✓" if r.proved() else "✗"
            print(f" {symbol} [{r.status:20s}] nodes={r.node_count}  ({r.elapsed_s:.3f}s)")

    return rows


def _status_to_tier(status: str) -> int:
    return {
        "proved_numerical":  1,
        "proved_certified":  3,
        "proved_exact":      2,
        "proved_witness":    4,
    }.get(status, 0)


# ── Random controls ───────────────────────────────────────────────────────────

def generate_random_controls(
    n:      int = 200,
    seed:   int = 0,
) -> list[dict]:
    """Generate random algebraic 1-variable functions as controls.

    Pool of primitives: constant, x, x², x³, x^0.5, x^1.5, exp(x), ln(x),
    1/x, 1/x², sin(x), cos(x), and their products/sums.
    """
    rng = random.Random(seed)

    def _safe(fn, domain, n_check=20):
        lo, hi = domain
        for _ in range(n_check):
            x = lo + (hi - lo) * rng.random()
            try:
                y = fn(x)
                if not math.isfinite(y):
                    return False
            except Exception:
                return False
        return True

    PRIMITIVES: list[tuple[str, Callable, tuple]] = [
        ("x",          lambda x: x,                  (0.5, 3.0)),
        ("x^2",        lambda x: x**2,               (0.5, 2.5)),
        ("x^3",        lambda x: x**3,               (0.5, 2.0)),
        ("sqrt(x)",    lambda x: x**0.5,             (0.5, 3.0)),
        ("x^1.5",      lambda x: x**1.5,             (0.5, 3.0)),
        ("exp(x)",     math.exp,                      (0.0, 2.5)),
        ("exp(-x)",    lambda x: math.exp(-x),        (0.0, 3.0)),
        ("exp(x^2)",   lambda x: math.exp(x**2),      (0.0, 1.5)),
        ("ln(x)",      math.log,                      (0.5, 4.0)),
        ("1/x",        lambda x: 1/x,                (0.5, 4.0)),
        ("1/x^2",      lambda x: 1/x**2,             (0.5, 3.0)),
        ("sin(x)",     math.sin,                      (-3.0, 3.0)),
        ("cos(x)",     math.cos,                      (-3.0, 3.0)),
        ("x*exp(-x)",  lambda x: x*math.exp(-x),      (0.0, 4.0)),
        ("x^2*exp(-x)",lambda x: x**2*math.exp(-x),   (0.0, 4.0)),
        ("1/(1+x^2)",  lambda x: 1/(1+x**2),          (0.0, 4.0)),
        ("exp(-x^2)",  lambda x: math.exp(-x**2),     (-2.0, 2.0)),
        ("ln(1+x)",    lambda x: math.log(1+x),        (0.0, 4.0)),
        ("x*ln(x)",    lambda x: x*math.log(x),        (0.5, 4.0)),
        ("1/(exp(x)-1)",lambda x: 1/(math.exp(x)-1),  (0.5, 3.0)),
    ]

    controls = []
    choices = rng.choices(PRIMITIVES, k=n)
    for name, fn, domain in choices:
        if not _safe(fn, domain):
            continue
        controls.append({"name": name, "fn": fn, "domain": domain})

    return controls[:n]


def census_controls(
    n:             int = 200,
    n_simulations: int = 800,
    seed:          int = 0,
    verbose:       bool = False,
) -> list[dict]:
    """Measure EML depth profile for random algebraic controls."""
    controls = generate_random_controls(n=n, seed=seed)
    rows = []
    for i, ctrl in enumerate(controls):
        profile = measure_eml_profile(
            ctrl["fn"], ctrl["domain"],
            depths=(2, 4, 6),
            n_simulations=n_simulations,
        )
        rows.append({"name": ctrl["name"], "category": "control", **profile})
        if verbose and (i + 1) % 20 == 0:
            print(f"  controls: {i+1}/{len(controls)}")
    return rows


# ── Rediscovery benchmark ─────────────────────────────────────────────────────

REDISCOVERY_LAWS: list[dict] = [
    {
        "name":      "Boltzmann weight",
        "fn":        lambda x: math.exp(x),
        "domain":    (0.0, 2.5),
        "n_data":    60,
        "noise":     0.03,
    },
    {
        "name":      "Radioactive decay",
        "fn":        lambda x: math.exp(-x),
        "domain":    (0.0, 3.0),
        "n_data":    60,
        "noise":     0.03,
    },
    {
        "name":      "Arrhenius (simplified)",
        "fn":        lambda x: math.exp(-1.0 / x),
        "domain":    (0.5, 4.0),
        "n_data":    60,
        "noise":     0.03,
    },
    {
        "name":      "Planck distribution",
        "fn":        lambda x: 1.0 / (math.exp(x) - 1.0),
        "domain":    (0.5, 3.0),
        "n_data":    60,
        "noise":     0.05,
    },
    {
        "name":      "Wien's law",
        "fn":        lambda x: 1.0 / x,
        "domain":    (0.5, 4.0),
        "n_data":    60,
        "noise":     0.03,
    },
    {
        "name":      "Kepler's 3rd law",
        "fn":        lambda x: x ** 1.5,
        "domain":    (0.5, 3.0),
        "n_data":    60,
        "noise":     0.02,
    },
    {
        "name":      "Stefan-Boltzmann",
        "fn":        lambda x: x ** 4,
        "domain":    (0.5, 2.0),
        "n_data":    60,
        "noise":     0.02,
    },
    {
        "name":      "Gaussian (ground state)",
        "fn":        lambda x: math.exp(-x * x),
        "domain":    (-2.0, 2.0),
        "n_data":    80,
        "noise":     0.02,
    },
]


def rediscovery_benchmark(
    verbose: bool = True,
) -> list[dict]:
    """Attempt to rediscover each physical law from synthetic noisy data.

    Uses :class:`~monogate.sklearn_wrapper.EMLRegressor` for fitting.

    Returns a list of result dicts with R², recovered formula, and
    whether the ground-truth formula was matched.
    """
    try:
        from monogate.sklearn_wrapper import EMLRegressor
    except ImportError:
        print("[warning] EMLRegressor not available — skipping rediscovery")
        return []

    rng = np.random.default_rng(seed=42)
    rows = []
    n = len(REDISCOVERY_LAWS)

    for i, law in enumerate(REDISCOVERY_LAWS):
        if verbose:
            print(f"  [{i+1}/{n}] {law['name']:35s} ...", end="", flush=True)

        lo, hi = law["domain"]
        x_data = np.linspace(lo, hi, law["n_data"])
        y_clean = np.array([law["fn"](x) for x in x_data])

        # Add Gaussian noise proportional to signal
        scale = np.std(y_clean) * law["noise"]
        noise = rng.normal(0, scale, size=y_clean.shape)
        y_noisy = y_clean + noise

        # Fit EMLRegressor
        t0 = time.perf_counter()
        try:
            reg = EMLRegressor(max_depth=2, n_simulations=2000)
            reg.fit(x_data.reshape(-1, 1), y_noisy)
            y_pred = reg.predict(x_data.reshape(-1, 1))
            elapsed = time.perf_counter() - t0

            # Compute R²
            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - y_clean.mean()) ** 2)
            r2 = 1.0 - ss_res / max(ss_tot, 1e-12)

            # Residual on clean data
            rmse = float(np.sqrt(np.mean((y_clean - y_pred) ** 2)))

            row = {
                "name":        law["name"],
                "r2":          float(r2),
                "rmse_clean":  rmse,
                "elapsed_s":   elapsed,
                "n_data":      law["n_data"],
                "noise_level": law["noise"],
            }

            if verbose:
                print(f" R²={r2:.3f}  rmse={rmse:.4f}  ({elapsed:.1f}s)")

        except Exception as exc:
            elapsed = time.perf_counter() - t0
            row = {
                "name":    law["name"],
                "r2":      None,
                "error":   str(exc),
                "elapsed_s": elapsed,
            }
            if verbose:
                print(f" ERROR: {exc}")

        rows.append(row)

    return rows


# ── Statistical comparison ────────────────────────────────────────────────────

def compare_laws_vs_controls(
    law_rows:     list[dict],
    control_rows: list[dict],
) -> dict:
    """Compute statistical comparison between law and control MSE profiles."""
    def _extract(rows, depth):
        key = f"depth_{depth}"
        vals = []
        for r in rows:
            mse = r.get(key, {}).get("mse", float("inf"))
            if math.isfinite(mse):
                vals.append(mse)
        return vals

    result = {}
    for d in (2, 4, 6):
        law_mse  = _extract(law_rows, d)
        ctrl_mse = _extract(control_rows, d)
        result[f"depth_{d}"] = {
            "law_mean":      float(np.mean(law_mse))     if law_mse  else None,
            "law_median":    float(np.median(law_mse))   if law_mse  else None,
            "control_mean":  float(np.mean(ctrl_mse))    if ctrl_mse else None,
            "control_median":float(np.median(ctrl_mse))  if ctrl_mse else None,
            "n_laws":        len(law_mse),
            "n_controls":    len(ctrl_mse),
        }

    # EML-native rate
    law_native = sum(1 for r in law_rows if r.get("eml_native"))
    ctrl_native = sum(1 for r in control_rows if r.get("eml_native"))
    result["native_rate"] = {
        "laws":    law_native / max(len(law_rows), 1),
        "controls": ctrl_native / max(len(control_rows), 1),
    }

    return result


# ── CLI / full census ─────────────────────────────────────────────────────────

def run_full_census(
    n_simulations:    int  = 1500,
    n_controls:       int  = 100,
    skip_rediscovery: bool = False,
    verbose:          bool = True,
) -> dict:
    """Run the complete Physics Law Complexity Census."""
    import json
    from pathlib import Path

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir   = Path("results/physics_census")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  PHYSICS LAW COMPLEXITY CENSUS")
    print("=" * 60)

    # 1 — Identity census
    print("\n[1/4] Identity census (prove each identity law)")
    print("-" * 50)
    identity_rows = census_identities(verbose=verbose)

    # 2 — Functional census
    print("\n[2/4] Functional census (EML depth profile)")
    print("-" * 50)
    functional_rows = census_functional(n_simulations=n_simulations, verbose=verbose)

    # 3 — Controls
    print(f"\n[3/4] Random controls ({n_controls} expressions)")
    print("-" * 50)
    control_rows = census_controls(
        n=n_controls, n_simulations=min(n_simulations, 800), verbose=verbose
    )

    # 4 — Rediscovery
    rediscovery_rows = []
    if not skip_rediscovery:
        print("\n[4/4] Rediscovery benchmark")
        print("-" * 50)
        rediscovery_rows = rediscovery_benchmark(verbose=verbose)

    # Comparison
    comparison = compare_laws_vs_controls(functional_rows, control_rows)

    # Assemble and save
    session = {
        "timestamp":      timestamp,
        "n_simulations":  n_simulations,
        "identity_census":   identity_rows,
        "functional_census": functional_rows,
        "control_census":    control_rows,
        "rediscovery":       rediscovery_rows,
        "comparison":        comparison,
    }

    # Strip non-serialisable fn references from controls
    safe_controls = [{k: v for k, v in r.items() if k != "fn"} for r in control_rows]
    safe_session  = {**session, "control_census": safe_controls}

    out_path = out_dir / f"census_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(safe_session, f, indent=2, default=str)

    # Print summary
    _print_summary(identity_rows, functional_rows, control_rows,
                   rediscovery_rows, comparison)
    print(f"\nResults: {out_path}")

    return session


def _print_summary(identity_rows, functional_rows, control_rows,
                   rediscovery_rows, comparison):
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    # Identity census
    proved = [r for r in identity_rows if r["status"].startswith("proved")]
    by_tier = {}
    for r in proved:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
    print(f"\nIdentity census ({len(identity_rows)} laws):")
    print(f"  Proved: {len(proved)}/{len(identity_rows)}")
    for tier, count in sorted(by_tier.items()):
        tier_name = {1:"numerical", 2:"exact", 3:"certified", 4:"witness"}.get(tier, "?")
        print(f"    Tier {tier} ({tier_name:10s}): {count}")

    # Functional census — EML-native laws
    native = [r for r in functional_rows if r.get("eml_native")]
    print(f"\nFunctional census ({len(functional_rows)} laws):")
    print(f"  EML-native (depth=1, MSE<1e-6): {len(native)}")
    for r in native:
        print(f"    {r['name']} [{r['category']}]")

    # Depth profile comparison
    print("\nMSE comparison (laws vs random controls):")
    for d in (2, 4, 6):
        c = comparison.get(f"depth_{d}", {})
        lm = c.get("law_mean")
        cm = c.get("control_mean")
        if lm is not None and cm is not None:
            ratio = lm / max(cm, 1e-12)
            indicator = "← laws LOWER" if ratio < 0.8 else ("≈ equal" if ratio < 1.3 else "← laws HIGHER")
            print(f"  Depth {d}: law_mean={lm:.3f}  ctrl_mean={cm:.3f}  ratio={ratio:.2f}  {indicator}")

    # Rediscovery
    if rediscovery_rows:
        good = [r for r in rediscovery_rows if r.get("r2") is not None and r["r2"] > 0.95]
        print(f"\nRediscovery benchmark ({len(rediscovery_rows)} laws):")
        print(f"  R² > 0.95: {len(good)}/{len(rediscovery_rows)}")
        for r in sorted(rediscovery_rows, key=lambda x: -(x.get("r2") or 0)):
            r2 = r.get("r2")
            r2_str = f"{r2:.3f}" if r2 is not None else "ERR"
            print(f"    {r['name']:35s}: R²={r2_str}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Physics Law Complexity Census"
    )
    parser.add_argument("--n-simulations", type=int, default=1500,
                        help="MCTS simulations per depth per law")
    parser.add_argument("--n-controls", type=int, default=100,
                        help="Number of random control expressions")
    parser.add_argument("--skip-rediscovery", action="store_true")
    parser.add_argument("--identity-only", action="store_true",
                        help="Only run identity census (fastest)")
    args = parser.parse_args()

    if args.identity_only:
        print("\n[Identity census only]\n" + "-" * 40)
        rows = census_identities(verbose=True)
        proved = sum(1 for r in rows if r["status"].startswith("proved"))
        print(f"\n{proved}/{len(rows)} proved")
    else:
        run_full_census(
            n_simulations=args.n_simulations,
            n_controls=args.n_controls,
            skip_rediscovery=args.skip_rediscovery,
        )


if __name__ == "__main__":
    main()
