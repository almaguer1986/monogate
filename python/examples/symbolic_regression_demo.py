"""
examples/symbolic_regression_demo.py
======================================
Clean symbolic regression demo using monogate.

Sections:
  1. Constants  — recover π, e, √2 with EMLTree(depth=3)
  2. Functions  — approximate x² with EMLNetwork(in_features=1, depth=2)
  3. BEST routing — best_optimize() on a SIREN-style expression
  4. PySR comparison — Nguyen-1 benchmark (optional, skipped if not installed)

Run from python/:
    python examples/symbolic_regression_demo.py
"""

import sys
import math

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import torch
except ImportError:
    print("ERROR: torch is required. Install it with:")
    print("  pip install torch")
    sys.exit(1)

from monogate.network import EMLTree, EMLNetwork, fit
from monogate import best_optimize

torch.manual_seed(42)

SEP = "=" * 56
DIV = "-" * 56


# ─────────────────────────────────────────────────────────────
# 1. CONSTANTS
# ─────────────────────────────────────────────────────────────

print()
print(SEP)
print("  1. Constant Recovery  (EMLTree, depth=3, lam=0.005)")
print(SEP)
print()
print("  lam=0.005 avoids phantom attractors (see research_02_attractors.py).")
print()

TARGETS = [
    ("pi",    math.pi),
    ("e",     math.e),
    ("sqrt2", math.sqrt(2)),
]

print(f"  {'Name':8} {'Target':>10} {'Found':>10} {'Error':>10}  Formula")
print("  " + DIV)

for name, target_val in TARGETS:
    target_tensor = torch.tensor(float(target_val))
    model = EMLTree(depth=3)
    fit(model, target=target_tensor, steps=2000, lr=1e-2, lam=0.005, log_every=0)
    found = model().item()
    err = abs(found - target_val)
    formula = model.formula()
    print(f"  {name:8} {target_val:>10.6f} {found:>10.6f} {err:>10.2e}  {formula[:40]}")

print()


# ─────────────────────────────────────────────────────────────
# 2. FUNCTIONS
# ─────────────────────────────────────────────────────────────

print(SEP)
print("  2. Function Approximation  (EMLNetwork, depth=2)")
print(SEP)
print()

x_train = torch.linspace(0.1, 3.0, 60)
X_train = x_train.unsqueeze(1)   # (60, 1)
Y_train = x_train ** 2            # target: x²

model_fn = EMLNetwork(in_features=1, depth=2)
losses = fit(model_fn, x=X_train, y=Y_train, steps=2000, lr=1e-2, lam=0.0, log_every=0)

# Loss milestones
milestones = [1, 200, 500, 1000, 2000]
print("  Training loss milestones (step → MSE):")
for step in milestones:
    idx = min(step - 1, len(losses) - 1)
    print(f"    step {step:>4}: {losses[idx]:.5f}")

# Final MSE on a held-out test set
x_test = torch.linspace(0.05, 3.5, 40)
X_test = x_test.unsqueeze(1)
Y_test = x_test ** 2
with torch.no_grad():
    Y_pred = model_fn(X_test)
test_mse = float(torch.mean((Y_pred - Y_test) ** 2))
print(f"\n  Final MSE on test set (40 points, x in [0.05, 3.5]): {test_mse:.5f}")
print()


# ─────────────────────────────────────────────────────────────
# 3. BEST ROUTING COMPARISON
# ─────────────────────────────────────────────────────────────

print(SEP)
print("  3. BEST Routing  (best_optimize on SIREN-style expression)")
print(SEP)
print()

siren_expr = "torch.sin(30 * x)**2 + torch.cos(x) * torch.pow(x, 3)"
print(f"  Expression: {siren_expr}")
print()

result = best_optimize(siren_expr)

# Savings table (built-in __str__ already formats nicely)
for line in str(result).splitlines():
    print(f"  {line}")

print()
print("  Rewritten code:")
for line in result.rewritten_code.splitlines():
    print(f"    {line}")
print()


# ─────────────────────────────────────────────────────────────
# 4. PYSR COMPARISON
# ─────────────────────────────────────────────────────────────

print(SEP)
print("  4. PySR Comparison  (Nguyen-1: x³+x²+x)")
print(SEP)
print()

try:
    from pysr import PySRRegressor
    import numpy as np

    x_raw = torch.linspace(-1.0, 1.0, 40)
    X_ng  = x_raw.unsqueeze(1)
    Y_ng  = x_raw ** 3 + x_raw ** 2 + x_raw

    # monogate
    model_ng = EMLNetwork(in_features=1, depth=2)
    losses_ng = fit(model_ng, x=X_ng, y=Y_ng, steps=2000, lr=1e-2, lam=0.0, log_every=0)
    mono_mse = losses_ng[-1]

    # PySR
    X_np = x_raw.numpy().reshape(-1, 1)
    y_np = Y_ng.numpy()
    pysr = PySRRegressor(
        niterations=40,
        verbosity=0,
        binary_operators=["+", "-", "*", "/", "^"],
        unary_operators=["sin", "cos", "exp", "log"],
    )
    pysr.fit(X_np, y_np)
    y_pred_pysr = pysr.predict(X_np)
    pysr_mse = float(np.mean((y_pred_pysr - y_np) ** 2))

    print(f"  {'Model':<16} {'Final MSE':>12}")
    print("  " + DIV[:32])
    print(f"  {'monogate':<16} {mono_mse:>12.5f}")
    print(f"  {'PySR':<16} {pysr_mse:>12.5f}")
    print()
    print(f"  PySR best expression: {pysr.latex()}")

except ImportError:
    print("  pip install pysr to enable PySR comparison")
    print()
    print("  Showing monogate-only result for Nguyen-1 (x³+x²+x):")
    x_raw = torch.linspace(-1.0, 1.0, 40)
    X_ng  = x_raw.unsqueeze(1)
    Y_ng  = x_raw ** 3 + x_raw ** 2 + x_raw
    model_ng = EMLNetwork(in_features=1, depth=2)
    losses_ng = fit(model_ng, x=X_ng, y=Y_ng, steps=2000, lr=1e-2, lam=0.0, log_every=0)
    print(f"  monogate final MSE: {losses_ng[-1]:.5f}")

print()
print(SEP)
print("  Done.")
print(SEP)
print()
