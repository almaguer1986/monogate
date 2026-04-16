"""
examples/symbolic_regression_full.py
=====================================
Comprehensive symbolic regression benchmark using monogate EML/BEST operators.

Covers:
  A. Constant recovery  — EMLTree fitting π, e, sqrt(2) with/without λ penalty
  B. Function fitting   — EMLNetwork on x², sin(x), and x*exp(-x)
  C. Operator comparison — EML vs BEST routing on sin-heavy targets
  D. PySR comparison    — head-to-head on two Nguyen benchmarks (if PySR installed)

Run from python/:
    python examples/symbolic_regression_full.py
    python examples/symbolic_regression_full.py --no-pysr   # skip PySR section
"""

import sys, math, time, argparse
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
from monogate.network import EMLTree, EMLNetwork, fit
from monogate.torch_ops import exl_op

torch.manual_seed(42)

SEP  = "-" * 58
SEP2 = "=" * 58

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Symbolic regression demo")
parser.add_argument("--no-pysr", action="store_true", help="Skip PySR comparison")
parser.add_argument("--steps",   type=int, default=3000, help="Training steps (default 3000)")
args = parser.parse_args()

STEPS = args.steps

# ── Helpers ───────────────────────────────────────────────────────────────────

def steps_to(losses, thr):
    for i, v in enumerate(losses):
        if v < thr:
            return i + 1
    return f">{STEPS}"


def run_emlnet(x, y, depth, op_func=None, label="", **kwargs):
    """Train EMLNetwork and return (model, losses, elapsed_s)."""
    kw = {"op_func": op_func} if op_func is not None else {}
    model = EMLNetwork(in_features=1, depth=depth, **kw)
    t0 = time.perf_counter()
    losses = fit(model, x=x, y=y, steps=STEPS, lr=1e-2, log_every=0, **kwargs)
    return model, losses, time.perf_counter() - t0


# ── Section A: Constant recovery ──────────────────────────────────────────────
print(SEP2)
print("  A. Constant recovery (EMLTree, depth=3)")
print(SEP2)
print()
print("  π uses ensemble probe (K=5 seeds × 250 steps, then refine best).")
print("  Other constants use single run with lam penalty.")
print()


def fit_constant(target_val: float, lam: float = 0.005,
                 steps: int = 3000, lr: float = 5e-3) -> tuple[float, float]:
    """Single-run constant recovery. Returns (found_value, final_loss)."""
    t = torch.tensor(float(target_val))
    model = EMLTree(depth=3)
    losses = fit(model, target=t, steps=steps, lr=lr, lam=lam, log_every=0)
    return model().item(), losses[-1]


def fit_constant_ensemble(target_val: float, k: int = 5,
                           probe_steps: int = 250, refine_steps: int = 3000,
                           lam: float = 0.005) -> tuple[float, float]:
    """
    Ensemble probe: K short runs, pick lowest loss, refine.
    Escapes dominant phantom attractors (documented in PAPER.md Section 5.2).
    """
    t = torch.tensor(float(target_val))
    probes = []
    for seed in range(k):
        torch.manual_seed(seed)
        m = EMLTree(depth=3)
        ls = fit(m, target=t, steps=probe_steps, lr=5e-3, lam=lam, log_every=0)
        probes.append((ls[-1], m))
    _, best_model = min(probes, key=lambda p: p[0])
    losses = fit(best_model, target=t, steps=refine_steps, lr=1e-3, lam=lam, log_every=0)
    return best_model().item(), losses[-1]


# π requires ensemble (100% trap without it, 100% escape with it + lam)
pi_found, pi_loss = fit_constant_ensemble(math.pi, k=5, lam=0.005)

CONST_TARGETS = [
    ("pi",    math.pi,       pi_found, "ensemble K=5", 5e-3),
    ("e",     math.e,        None,     "single,lam=0.001", 1e-2),
    ("sqrt2", math.sqrt(2),  None,     "single,lam=0.005", 2e-3),
    ("ln2",   math.log(2),   None,     "single,lam=0.005", 5e-3),
]

print(f"  {'Target':8} {'Actual':>10} {'Found':>10} {'Error':>10} {'Threshold':>10} {'Method':>18} {'OK?':>4}")
print("  " + "-" * 72)
for name, target, precomputed, method, thr in CONST_TARGETS:
    if precomputed is not None:
        found = precomputed
    elif "lam=0.001" in method:
        found, _ = fit_constant(target, lam=0.001)
    else:
        found, _ = fit_constant(target, lam=0.005)
    err = abs(found - target)
    ok = "YES" if err < thr else "NO "
    print(f"  {name:8} {target:>10.6f} {found:>10.6f} {err:>10.2e} {thr:>10.0e} {method:>18} {ok:>4}")

# ── Section B: Function fitting ───────────────────────────────────────────────
print()
print(SEP2)
print("  B. Function fitting (EMLNetwork, depth=3)")
print(SEP2)
print()

FUNCTIONS = [
    ("x^2",      torch.linspace(0.1, 3.0, 60),  lambda x: x**2),
    ("sin(x)",   torch.linspace(0.0, 6.28, 80), lambda x: torch.sin(x)),
    ("x*exp(-x)",torch.linspace(0.0, 4.0, 60),  lambda x: x * torch.exp(-x)),
]

print(f"  {'Function':14} {'Final MSE':>10} {'Steps<0.01':>10} {'Time(s)':>8}")
print("  " + "-" * 48)
for fname, x_raw, f in FUNCTIONS:
    X = x_raw.unsqueeze(1)
    Y = f(x_raw)
    model, losses, elapsed = run_emlnet(X, Y, depth=3, lam=0.001)
    print(
        f"  {fname:14} {losses[-1]:>10.5f} {steps_to(losses, 0.01):>10} {elapsed:>8.2f}"
    )

# ── Section C: EML vs BEST routing on sin(x) ─────────────────────────────────
print()
print(SEP2)
print("  C. EML vs BEST routing on sin(x) (depth=3, 80 points)")
print(SEP2)
print()

X_sin = torch.linspace(0.0, 6.28, 80).unsqueeze(1)
Y_sin = torch.sin(X_sin.squeeze())

print("  Training EML routing  (default eml_op)...")
m_eml, l_eml, t_eml = run_emlnet(X_sin, Y_sin, depth=3, lam=0.001)

print("  Training BEST routing (exl_op)...")
m_best, l_best, t_best = run_emlnet(X_sin, Y_sin, depth=3, op_func=exl_op, lam=0.001)

print()
print(f"  {'':28} {'EML':>10} {'BEST (EXL)':>12}")
print("  " + "-" * 52)
print(f"  {'Final MSE':28} {l_eml[-1]:>10.5f} {l_best[-1]:>12.5f}")
print(f"  {'Steps to MSE < 0.1':28} {steps_to(l_eml, 0.1):>10} {steps_to(l_best, 0.1):>12}")
print(f"  {'Steps to MSE < 0.01':28} {steps_to(l_eml, 0.01):>10} {steps_to(l_best, 0.01):>12}")
print(f"  {'Train time (s)':28} {t_eml:>10.2f} {t_best:>12.2f}")
print()

# Node costs for the dominant op (sin Taylor approximation)
from monogate.optimize import _BEST_NODES, _EML_NODES
sin_eml_n  = _EML_NODES.get("sin", 245)
sin_best_n = _BEST_NODES.get("sin", 63)
savings = round((1 - sin_best_n / sin_eml_n) * 100)
print(f"  sin node count: EML={sin_eml_n}n  BEST={sin_best_n}n  ({savings}% fewer)")
print(f"  EML  formula: {m_eml.formula(['x'])[:60]}")
print(f"  BEST formula: {m_best.formula(['x'])[:60]}")

# ── Section D: PySR comparison ────────────────────────────────────────────────
print()
print(SEP2)
print("  D. PySR comparison (Nguyen-style benchmarks)")
print(SEP2)
print()

if args.no_pysr:
    print("  [skipped — pass without --no-pysr to run]")
else:
    try:
        from pysr import PySRRegressor
        HAS_PYSR = True
    except ImportError:
        HAS_PYSR = False
        print("  PySR not installed — pip install pysr")
        print("  Showing monogate-only results for these benchmarks.")
        print()

    # Nguyen-3: x^3 + x^2 + x
    # Nguyen-5: sin(x^2) * cos(x) - 1
    BENCHMARKS = [
        ("Nguyen-3", "x^3+x^2+x",    torch.linspace(-1.0, 1.0, 40),
         lambda x: x**3 + x**2 + x),
        ("Nguyen-5", "sin(x^2)cos(x)-1", torch.linspace(-1.0, 1.0, 40),
         lambda x: torch.sin(x**2) * torch.cos(x) - 1),
    ]

    print(f"  {'Benchmark':16} {'Target':20} {'monogate MSE':>13} {'PySR MSE':>10}")
    print("  " + "-" * 62)
    for bname, bexpr, x_raw, f in BENCHMARKS:
        X_b = x_raw.unsqueeze(1)
        Y_b = f(x_raw)
        m_b, l_b, _ = run_emlnet(X_b, Y_b, depth=3, op_func=exl_op, lam=0.001)
        mono_mse = l_b[-1]

        pysr_mse = float("nan")
        if HAS_PYSR:
            try:
                import numpy as np
                X_np = x_raw.numpy().reshape(-1, 1)
                y_np = Y_b.numpy()
                pysr = PySRRegressor(niterations=40, verbosity=0,
                                     binary_operators=["+", "-", "*", "/", "^"],
                                     unary_operators=["sin", "cos", "exp", "log"])
                pysr.fit(X_np, y_np)
                y_pred = pysr.predict(X_np)
                pysr_mse = float(np.mean((y_pred - y_np)**2))
            except Exception as exc:
                pysr_mse = float("nan")
                print(f"    PySR failed for {bname}: {exc}")

        pysr_str = f"{pysr_mse:.5f}" if not math.isnan(pysr_mse) else "n/a"
        print(f"  {bname:16} {bexpr:20} {mono_mse:>13.5f} {pysr_str:>10}")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(SEP2)
print("  Summary")
print(SEP2)
print()
print("  EMLTree constant recovery (depth=3, stochastic):")
print("    Ensemble probe (K=5 seeds) + lam penalty escapes dominant attractors.")
print("    Without lam: 100% of seeds converge to wrong attractor (~3.1696).")
print("    With lam=0.005: 20/20 converge (research_02_attractors.py, 40-seed study).")
print()
print("  EMLNetwork function fitting:")
print("    BEST (EXL) routing reaches convergence thresholds faster than EML.")
print("    Final MSE advantage depends on the loss landscape; EXL can converge")
print("    to different local minima due to different gradient geometry.")
print()
print("  Practical guidance:")
print("    - Use lam >= 0.005 for constant targets (EMLTree)")
print("    - Use op_func=exl_op for sin/cos/pow-heavy function fitting")
print("    - BEST routing: 74% node reduction on sin, 80% on pow — 2.8-3.4x speedup")
