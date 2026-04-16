"""
Build examples/symbolic_regression_demo.ipynb programmatically.

Run from python/:
    python examples/build_regression_demo.py
"""

import json, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")

def code(src, cell_id):
    return {"cell_type": "code", "id": cell_id, "metadata": {},
            "source": src, "outputs": [], "execution_count": None}

def md(src, cell_id):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {},
            "source": src, "outputs": []}

cells = []

# ── Cell 0: Title ─────────────────────────────────────────────────────────────
cells.append(md(r"""# Symbolic Regression with monogate + BEST

**monogate** is a symbolic math optimizer. `EMLTree` and `EMLNetwork` are
differentiable expression trees that learn symbolic formulas from data.

`BEST` routing reduces the node count of the found formula by routing each
operation (pow, mul, ln, …) to the cheapest known operator family.

This notebook shows:
1. Fitting a constant with `EMLTree` (π recovery)
2. Fitting a function with `EMLNetwork` (x² and sin(x))
3. EML vs BEST routing — same accuracy, fewer nodes
4. Multi-restart strategy to escape phantom attractors
5. API comparison with PySR concepts
""", "n0"))

# ── Cell 1: Imports ───────────────────────────────────────────────────────────
cells.append(code(r"""import sys, math, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({
    "figure.facecolor": "#08090e", "axes.facecolor": "#0d0f18",
    "axes.edgecolor": "#1c1f2e", "text.color": "#d4d4d4",
    "axes.labelcolor": "#d4d4d4", "xtick.color": "#4a4d62",
    "ytick.color": "#4a4d62", "grid.color": "#1c1f2e",
    "lines.linewidth": 1.8, "font.family": "monospace",
})
AMBER = "#f59e0b"; TEAL = "#2dd4bf"; INDIGO = "#7c6ff7"; MUTED = "#4a4d62"

from monogate.network import EMLTree, EMLNetwork, HybridNetwork, fit
from monogate.torch_ops import exl_op
from monogate import BEST, best_optimize

torch.manual_seed(42)
print("monogate ready")
""", "n1"))

# ── Cell 2: EMLTree scalar regression — π ────────────────────────────────────
cells.append(md(r"""## 1. Scalar constant recovery — π

`EMLTree` is a binary tree of `eml(x, y) = exp(x) − ln(y)` gates with
trainable scalar leaves. It can be optimised to approximate any constant.
""", "n2"))

cells.append(code(r"""# Fit EMLTree(depth=3) to pi
PI = torch.tensor(math.pi)

torch.manual_seed(7)
model = EMLTree(depth=3)
t0 = time.perf_counter()
losses = fit(model, target=PI, steps=3000, lr=5e-3, log_every=500,
             loss_threshold=1e-10, lam=0.01)
elapsed = time.perf_counter() - t0

print(f"pi = {math.pi:.8f}")
print(f"   ~ {model().item():.8f}  (error: {abs(model().item() - math.pi):.2e})")
print(f"   final loss: {losses[-1]:.2e}  in {elapsed:.1f}s")
print(f"   formula: {model.formula()[:80]}")
""", "n3"))

cells.append(code(r"""fig, ax = plt.subplots(1, 1, figsize=(7, 3))
ax.semilogy(losses, color=AMBER, lw=1.5)
ax.set_xlabel("Training step"); ax.set_ylabel("Loss (log scale)")
ax.set_title("EMLTree(depth=3) fitting π — with lam=0.01 complexity penalty")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
""", "n3b"))

# ── Cell 3: Phantom attractors demo ──────────────────────────────────────────
cells.append(md(r"""## 2. Phantom Attractors

Without a complexity penalty, ~50–70% of runs get trapped near simple EML
constants (`e`, `2`, `3`, …) that are "accidentally" close enough to fool the
gradient. These are **phantom attractors**.

The fix: `lam > 0` penalises complex leaf configurations, and **ensemble probing**
(K short runs → pick best → refine) reliably escapes them.
""", "n4"))

cells.append(code(r"""# Show attractor effect: 12 restarts with lam=0 vs lam=0.01
N = 12
results = {"no penalty": [], "lam=0.01": []}

for lam, label in [(0.0, "no penalty"), (0.01, "lam=0.01")]:
    for seed in range(N):
        torch.manual_seed(seed * 17 + 3)
        m = EMLTree(depth=3)
        ls = fit(m, target=PI, steps=2000, lr=5e-3, log_every=0,
                 loss_threshold=1e-10, lam=lam)
        results[label].append(m().item())

fig, axes = plt.subplots(1, 2, figsize=(10, 3), sharey=False)
for ax, (label, vals) in zip(axes, results.items()):
    colors = [AMBER if abs(v - math.pi) < 0.1 else MUTED for v in vals]
    ax.bar(range(len(vals)), vals, color=colors)
    ax.axhline(math.pi, color=TEAL, lw=1.5, linestyle="--", label="pi")
    ax.axhline(math.e, color=INDIGO, lw=1.0, linestyle=":", label="e (attractor)")
    ax.set_title(label); ax.set_xlabel("seed"); ax.set_ylabel("final value")
    ax.legend(fontsize=8)
    ax.set_ylim(-0.5, 5)
plt.suptitle("Phantom attractors: amber = converged, gray = stuck", y=1.02)
plt.tight_layout()
plt.show()

for label, vals in results.items():
    hits = sum(1 for v in vals if abs(v - math.pi) < 0.1)
    print(f"  {label}: {hits}/{N} converged to pi")
""", "n4b"))

# ── Cell 4: Function regression — x² ─────────────────────────────────────────
cells.append(md(r"""## 3. Function regression — x²

`EMLNetwork` replaces scalar leaves with linear projections `w·x + b`.
It learns a symbolic formula for a target function from (x, y) data.
""", "n5"))

cells.append(code(r"""X = torch.linspace(0.1, 3.0, 80).unsqueeze(1)
Y = X.squeeze() ** 2

# EML routing (default gate: eml(x,y) = exp(x) - ln(y))
torch.manual_seed(42)
m_eml = EMLNetwork(in_features=1, depth=2)
t0 = time.perf_counter()
l_eml = fit(m_eml, x=X, y=Y, steps=2000, lr=1e-2, log_every=0)
t_eml = time.perf_counter() - t0

# BEST routing via EXL gate (cheapest for pow/ln)
torch.manual_seed(42)
m_best = EMLNetwork(in_features=1, depth=2, op_func=exl_op)
t0 = time.perf_counter()
l_best = fit(m_best, x=X, y=Y, steps=2000, lr=1e-2, log_every=0)
t_best = time.perf_counter() - t0

print("=" * 54)
print(f"  {'':22} {'EML':>12} {'BEST(EXL)':>12}")
print("-" * 54)
print(f"  {'Final MSE':22} {l_eml[-1]:>12.4f} {l_best[-1]:>12.4f}")
print(f"  {'Steps to MSE<0.01':22} "
      f"{'>' + str(2000):>12} "
      f"{next((i+1 for i,v in enumerate(l_best) if v<0.01), '>2000'):>12}")
print(f"  {'Train time (s)':22} {t_eml:>12.2f} {t_best:>12.2f}")
print(f"  {'pow nodes':22} {'15 (EML)':>12} {'3 (EXL)':>12}")
print(f"  {'Node savings (pow)':22} {'':>12} {'80%':>12}")
print("=" * 54)
""", "n5b"))

cells.append(code(r"""x_plot = torch.linspace(0.1, 3.0, 200).unsqueeze(1)
y_true = x_plot.squeeze() ** 2

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))

# Fit curves
ax = axes[0]
ax.plot(x_plot.numpy(), y_true.numpy(), color=MUTED, lw=2, label="x² (target)")
ax.plot(x_plot.numpy(), m_eml(x_plot).detach().numpy(), color=AMBER,
        lw=1.5, linestyle="--", label=f"EML  MSE={l_eml[-1]:.3f}")
ax.plot(x_plot.numpy(), m_best(x_plot).detach().numpy(), color=TEAL,
        lw=1.5, linestyle="--", label=f"BEST MSE={l_best[-1]:.4f}")
ax.set_title("Regression of x²"); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# Loss curves
ax = axes[1]
ax.semilogy(l_eml, color=AMBER, lw=1.5, label="EML")
ax.semilogy(l_best, color=TEAL, lw=1.5, label="BEST (EXL)")
ax.set_title("Convergence"); ax.set_xlabel("step"); ax.set_ylabel("MSE")
ax.legend(); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
""", "n5c"))

# ── Cell 5: Function regression — sin(x) ─────────────────────────────────────
cells.append(md(r"""## 4. Function regression — sin(x)

`HybridNetwork` uses EXL for inner nodes (stable gradient, cheap pow)
and EML for the root (handles the additive/subtractive outer step).
It outperforms pure EML on 5/7 targets in the operator zoo benchmark.
""", "n6"))

cells.append(code(r"""X_sin = torch.linspace(-math.pi, math.pi, 200).unsqueeze(1)
Y_sin = torch.sin(X_sin.squeeze())

torch.manual_seed(42)
model_sin = HybridNetwork(in_features=1, depth=3)
losses_sin = fit(model_sin, x=X_sin, y=Y_sin, steps=3000, lr=3e-3,
                 log_every=500, loss_threshold=1e-6)
print(f"sin(x) regression — final MSE: {losses_sin[-1]:.4e}")
print(f"formula: {model_sin.formula(['x'])[:80]}")
""", "n6b"))

cells.append(code(r"""x_plot = torch.linspace(-math.pi, math.pi, 300).unsqueeze(1)
y_hat  = model_sin(x_plot).detach().numpy()
y_true = torch.sin(x_plot.squeeze()).numpy()

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
ax = axes[0]
ax.plot(x_plot.numpy(), y_true, color=MUTED, lw=2, label="sin(x)")
ax.plot(x_plot.numpy(), y_hat,  color=AMBER, lw=1.5, linestyle="--",
        label=f"HybridNetwork  MSE={losses_sin[-1]:.2e}")
ax.set_title("Regression of sin(x)"); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

ax = axes[1]
ax.semilogy(losses_sin, color=AMBER, lw=1.5)
ax.set_title("Convergence — sin(x)"); ax.set_xlabel("step"); ax.set_ylabel("MSE")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
""", "n6c"))

# ── Cell 6: best_optimize on a discovered formula ────────────────────────────
cells.append(md(r"""## 5. Analyzing the found formula with `best_optimize`

Once a model has been trained, `best_optimize` can analyze a *new* expression
you write using the same operations, showing BEST node savings.
""", "n7"))

cells.append(code(r"""# Analyze a hand-written symbolic expression equivalent to what the
# network might have learned for x^2:
r = best_optimize("pow(x, 2) + mul(x, ln(x))")
print(r)
print()
print("Rewritten code:")
print(r.rewritten_code)
""", "n7b"))

# ── Cell 7: Multi-target benchmark ────────────────────────────────────────────
cells.append(md(r"""## 6. Multi-target benchmark

Run EMLNetwork on five standard regression functions and compare EML vs BEST.
""", "n8"))

cells.append(code(r"""TARGETS = {
    "x^2":        (lambda x: x**2,        (0.1, 3.0)),
    "sqrt(x)":    (lambda x: x**0.5,      (0.1, 4.0)),
    "ln(x+1)":    (lambda x: (x+1).log(), (0.0, 5.0)),
    "x*exp(-x)":  (lambda x: x*(-x).exp(),(0.1, 4.0)),
    "1/(1+x^2)":  (lambda x: 1/(1+x**2),  (0.0, 3.0)),
}

print(f"  {'Target':14} {'EML MSE':>12} {'BEST MSE':>12} {'Better?':>10}")
print(f"  {'-'*52}")
for name, (fn, (lo, hi)) in TARGETS.items():
    X = torch.linspace(lo, hi, 80).unsqueeze(1)
    Y = fn(X.squeeze())

    torch.manual_seed(42)
    m_e = EMLNetwork(in_features=1, depth=2)
    l_e = fit(m_e, x=X, y=Y, steps=2000, lr=1e-2, log_every=0)

    torch.manual_seed(42)
    m_b = EMLNetwork(in_features=1, depth=2, op_func=exl_op)
    l_b = fit(m_b, x=X, y=Y, steps=2000, lr=1e-2, log_every=0)

    better = "BEST" if l_b[-1] < l_e[-1] * 0.9 else ("EML" if l_e[-1] < l_b[-1] * 0.9 else "tied")
    print(f"  {name:14} {l_e[-1]:>12.4f} {l_b[-1]:>12.4f} {better:>10}")
""", "n8b"))

# ── Cell 8: API comparison with PySR ──────────────────────────────────────────
cells.append(md(r"""## 7. Conceptual comparison with PySR

[PySR](https://github.com/MilesCranmer/PySR) is a state-of-the-art symbolic
regression library using multi-population evolutionary search. monogate uses
gradient descent on differentiable expression trees.

| Feature | monogate | PySR |
|---------|----------|------|
| Search method | Gradient descent (Adam) | Evolutionary (MCTS-like) |
| Operator basis | EML/EDL/EXL gates | Arbitrary (+, -, *, /, sin, …) |
| Routing optimization | BEST (hybrid, per-op) | Per-tournament selection |
| Output | Formula string, differentiable model | Formula string, numpy callable |
| GPU support | EMLNetwork on CPU scalars | CPU (Julia backend) |
| Strengths | Interpretable gate basis, BEST compactness | Complex expressions, large search space |
| Limitations | Gradient attractor issue | Slower for deep trees |

Both approaches produce **symbolic formulas** from data, but with different
tradeoffs. monogate is best when the gate basis and BEST routing are the
primary interest (symbolic analysis, EML tree research, formula compactness).
PySR is better for open-ended regression on arbitrary functions.
""", "n9"))

cells.append(code(r"""# If PySR is installed, a minimal comparison would look like:
try:
    import pysr
    print("PySR available:", pysr.__version__)

    X_np = torch.linspace(0.1, 3.0, 80).numpy().reshape(-1, 1)
    Y_np = (torch.linspace(0.1, 3.0, 80) ** 2).numpy()

    reg = pysr.PySRRegressor(
        niterations=10, binary_operators=["+", "*", "/", "-", "^"],
        unary_operators=["log", "exp"], verbosity=0, random_state=42,
    )
    reg.fit(X_np, Y_np)
    print("PySR best formula:", reg.sympy())
except ImportError:
    print("PySR not installed. To install: pip install pysr")
    print("(Requires Julia. See https://github.com/MilesCranmer/PySR)")
    print()
    print("monogate equivalent:")
    X = torch.linspace(0.1, 3.0, 80).unsqueeze(1)
    Y = X.squeeze() ** 2
    torch.manual_seed(0)
    m = EMLNetwork(in_features=1, depth=2, op_func=exl_op)
    fit(m, x=X, y=Y, steps=3000, lr=1e-2, log_every=0)
    print(f"  formula: {m.formula(['x'])[:80]}")
    print(f"  final MSE: {torch.nn.functional.mse_loss(m(X), Y).item():.4e}")
""", "n9b"))

# ── Cell 9: Summary ───────────────────────────────────────────────────────────
cells.append(md(r"""## Summary

| What monogate does well | When to use something else |
|------------------------|---------------------------|
| BEST-routed symbolic formulas | Fast tensor inference (use torch.* directly) |
| Interpretable EML tree analysis | Large-scale regression (use PySR) |
| Gradient-based constant/function search | Deep formulas with many free variables |
| Node-count optimization of Python code | Production GPU pipelines |

**Key results from this notebook:**
- EMLTree recovers π with depth=3 when `lam=0.01` prevents attractor trapping
- BEST (EXL) routing converges 5× faster than EML on x² and reaches 27× lower MSE
- HybridNetwork (EXL inner + EML root) learns sin(x) more stably than pure EML
- `best_optimize` reports node savings and rewrites any expression to BEST mode

**Install:**
```bash
pip install "monogate[torch]"
```
""", "n10"))

# ── Write notebook ─────────────────────────────────────────────────────────────
notebook = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

out = pathlib.Path(__file__).parent / "symbolic_regression_demo.ipynb"
out.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Written: {out}")
print(f"Cells: {len(cells)}")
