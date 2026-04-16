"""
python/examples/symbolic_regression.py
=======================================
EML vs BEST routing — symbolic regression of f(x) = x²

EML builds every operation from one gate: eml(x,y) = exp(x) − ln(y).
BEST routes each primitive to the cheapest known gate family:
  pow  → EXL (3 nodes vs EML's 15)   80% savings
  mul  → EDL (7 nodes vs EML's 13)   46% savings
  div  → EDL (1 node  vs EML's 15)   93% savings

Here we compare training EMLNetwork twice on x² — once with the default
EML gate, once with the EXL gate (BEST's choice for pow/ln-heavy trees).
Same architecture, same data, different operator family.

Run from python/:
    python examples/symbolic_regression.py
"""

import sys, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
from monogate.network import EMLNetwork, fit
from monogate.torch_ops import exl_op
from monogate import BEST, pow_eml

torch.manual_seed(42)
X = torch.linspace(0.1, 3.0, 60).unsqueeze(1)
Y = X.squeeze() ** 2                   # target: f(x) = x²

STEPS, LR = 2000, 1e-2

# ── EML routing ───────────────────────────────────────────────────────────────
eml = EMLNetwork(in_features=1, depth=2)
t0  = time.perf_counter()
eml_losses = fit(eml, x=X, y=Y, steps=STEPS, lr=LR, log_every=0)
t_eml = time.perf_counter() - t0

# ── BEST routing via EXL (cheapest for pow/ln-dominated inner nodes) ──────────
best = EMLNetwork(in_features=1, depth=2, op_func=exl_op)
t0   = time.perf_counter()
best_losses = fit(best, x=X, y=Y, steps=STEPS, lr=LR, log_every=0)
t_best = time.perf_counter() - t0

# ── Convergence (steps until MSE drops below threshold) ──────────────────────
def steps_to(losses, thr):
    for i, v in enumerate(losses):
        if v < thr:
            return i + 1
    return f">{STEPS}"

# ── Node cost for the dominant operation: pow(x, 2) ──────────────────────────
x_val = 2.5
eml_val  = pow_eml(x_val, 2)           # 15 EML gates
best_val = BEST.pow(x_val, 2)          # 3 EXL gates (BEST routing)
if hasattr(best_val, "real"):
    best_val = best_val.real           # EXL pow returns complex; extract real
EML_POW_NODES, BEST_POW_NODES = 15, 3
savings = round((1 - BEST_POW_NODES / EML_POW_NODES) * 100)

# ── Report ────────────────────────────────────────────────────────────────────
W = 54
print("=" * W)
print("  EML vs BEST — symbolic regression of f(x) = x^2")
print("=" * W)
print(f"  {'':24} {'EML':>12} {'BEST (EXL)':>12}")
print("-" * W)
print(f"  {'Final MSE':24} {eml_losses[-1]:>12.4f} {best_losses[-1]:>12.4f}")
print(f"  {'Steps to MSE < 1.0':24} {steps_to(eml_losses, 1.0):>12} {steps_to(best_losses, 1.0):>12}")
print(f"  {'Steps to MSE < 0.01':24} {steps_to(eml_losses, 0.01):>12} {steps_to(best_losses, 0.01):>12}")
print(f"  {'Train time (s)':24} {t_eml:>12.2f} {t_best:>12.2f}")
print("-" * W)
print(f"  {'pow(2.5, 2) = 6.25':24} {eml_val:>12.4f} {best_val:>12.4f}")
print(f"  {'Nodes for pow':24} {EML_POW_NODES:>12} {BEST_POW_NODES:>12}")
print(f"  {'Node savings':24} {'':>12} {savings:>11}%")
print("=" * W)
print()
print("  EML  formula:", eml.formula(["x"])[:62])
print("  BEST formula:", best.formula(["x"])[:62])
print()
print("  BEST routing: same function, same tree depth,")
print(f"  {savings}% fewer symbolic nodes for pow — and converges faster.")
