# monogate

monogate finds the most compact symbolic representation of elementary functions using a hybrid operator router (BEST).

```
eml(x, y) = exp(x) − ln(y)       ← the one gate
```

From this single binary operator and the constant `1`, every elementary function is an exact expression tree — no look-up tables, no approximation for the core identities. BEST routing then dispatches each primitive to whichever of three operator families (EML, EDL, EXL) uses the fewest nodes.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).  
Live explorer: **[monogate.dev](https://monogate.dev)**

---

## What's new in v0.9.0

- **Phantom attractor landscape visualization** — `plot_attractor_landscape.py` generates a 2D MSE loss-surface slice showing the wide false basin (~3.1696) and the narrow π basin, with three L1-penalty contour overlays. Run `python python/experiments/plot_attractor_landscape.py` to reproduce the paper figure.
- **Preprint §5.5** — new subsection explaining the geometric reason gradient-based search fails: basin geometry, L1 tilt effect, and implications for exact-function search.
- **Preprint: emlbox highlight** — the Infinite Zeros Barrier section now includes a styled callout box with theorem, proof, complex bypass equation, and `sin_via_euler` usage example.
- **`context_aware_best_optimize()`** — new public API wrapping `best_optimize()` with optional AST depth analysis and NumPy forward profiling. Detects risky deep subtraction chains, NaN/Inf, and high dynamic range before you commit to a routing choice.

```python
from monogate import context_aware_best_optimize
import numpy as np

r = context_aware_best_optimize(
    "exp(x) - exp(-x)",
    dynamic=True,
    sample_inputs=np.linspace(-50, 50, 500),
    warn=False,
)
print(r.diagnostics)   # {'savings_pct': 0, 'has_inf': True, ...}
for issue in r.stability_issues:
    print(issue)       # [SUB] depth>threshold: catastrophic cancellation risk
```

---

## Who this is for

monogate delivers measurable speedups on workloads dominated by **sin, cos, pow, ln** in the EML arithmetic substrate:

| Workload | Savings | Speedup |
|----------|---------|---------|
| SIREN / NeRF (sin activation) | 74% | **3.4×** |
| Physics ML (sin + pow-heavy) | 74% | **2.8–3.4×** |
| Polynomial activations (x⁴+x³+x²) | 54% | **2.1×** |
| Transformer FFN (GELU) | 18% | 0.93× — below crossover |

Crossover threshold: **~20% node reduction**. Below that, Python function-call overhead dominates any gate savings.

monogate is **not** a PyTorch inference accelerator. Native `torch.sin` is ~9,000× faster than any EML variant. This is a symbolic math optimizer for EML-substrate code, interpretable regression, and formal expression research.

---

## Install

**Python**
```bash
pip install monogate                # v0.3.0 — core only, no dependencies
pip install "monogate[torch]"       # + PyTorch ops, EMLTree, EMLNetwork, HybridNetwork
```

**JavaScript / Node**
```bash
npm install monogate                # v0.2.0 — EML, EDL, EXL, BEST, sin_best, cos_best
```

---

## What it does

monogate provides two things:

1. **A formal symbolic substrate.** Every elementary function (exp, ln, sin, cos, pow, div, …) is expressed as a finite tree of identical `eml(x,y)` gates. The tree is exact — no floating-point approximation beyond what the standard `exp`/`ln` functions introduce.

2. **BEST routing.** For each operation, three operator families are known. BEST dispatches to the cheapest one:

| Operation | BEST family | BEST nodes | EML baseline | Saving |
|-----------|-------------|-----------|--------------|--------|
| pow | EXL | 3 | 15 | −12 |
| div | EDL | 1 | 15 | −14 |
| mul | EDL | 7 | 13 | −6 |
| ln  | EXL | 1 | 3  | −2 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | — |
| add | EML | 11 | 11 | — |

Total for all nine primitives: **37 nodes** (BEST) vs 77 (all-EML) — 52% fewer.

---

## Quick start

**Python**
```python
from monogate import BEST, best_optimize

# BEST routing — cheapest gate per operation
BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs 15)
BEST.ln(2.718)        # ~1.0    (EXL, 1 node  vs 3)
BEST.add(3.0, 4.0)    # 7.0     (EML, 11 nodes — irreducible)

# Code optimizer — analyze any Python/NumPy/PyTorch expression
r = best_optimize("torch.sin(x)**2 + torch.cos(x) * x**3")
print(r)              # table + speedup indicator
print(r.rewritten_code)   # 72% fewer nodes
```

**JavaScript**
```js
import { BEST } from "monogate";

BEST.pow(2, 10);   // 1024  (EXL, 3 nodes)
BEST.div(6, 2);    // 3     (EDL, 1 node)
```

---

## Research results

**Phantom attractors in EMLTree optimization.**  
Gradient descent on depth-3 EML trees targeting π converges to the wrong value in 100% of random seeds without regularization. A small L1 penalty (λ=0.005) eliminates the attractor completely — 100% of runs converge. Full study: `python/experiments/research_02_attractors.py`.

**Exact sin(x) — exhaustive search.**  
All 862,116 EML trees with up to 8 internal nodes (terminals `{1, x}`) were enumerated. No tree matches sin(x) at any tolerance. A structural argument — the *Infinite Zeros Barrier* — proves no finite real-valued EML tree can represent sin(x) for any N: such trees have at most finitely many zeros, while sin has infinitely many.

We conjecture: **no finite EML tree with terminal `{1}` evaluates to exactly sin(x) for all real x.**

**EDL completeness.**  
EDL (`exp(x)/ln(y)`) is complete over the multiplicative elementary functions (div, mul, pow, recip, ln) but cannot construct addition or subtraction. Exhaustive search over 196 EDL trees from terminal `{e}` (N≤6) confirms no tree evaluates to any additive combination. EML and EDL are complementary — BEST routes optimally to each.

---

## When to use it

BEST routing pays off when your workload:

- Does symbolic regression or interpretable expression search
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Uses sin/cos activations (NeRF, SIREN, Fourier features, physics ML)
- Evaluates the same expression repeatedly across many inputs
- Needs human-readable formula output from a differentiable tree

Concrete starting point: [python/examples/symbolic_regression.py](python/examples/symbolic_regression.py) — EML vs BEST on x², side by side.

---

## When NOT to use it

**monogate is not a PyTorch inference accelerator.**

Native `torch.sin` is approximately **9,000× faster** than any EML variant (measured: 5 ms vs 47,000 ms for the same SIREN forward pass — experiment_12). The EML substrate computes in Python scalars via `math.exp` / `math.log`. It cannot compete with C++/BLAS.

Do not reach for monogate when:
- Your primary goal is fast tensor inference
- You are already using `torch.*` or `numpy.*` operations
- The total node reduction would be under ~20% (GELU at 18% is the concrete example)
- Your primary operations are `add` or `sub` (no savings — EML is already optimal)

monogate is the right tool for **symbolic analysis, formula construction, interpretable regression, and research into operator families.** It is not a drop-in replacement for production ML inference.

---

## Explorer (monogate.dev)

| Tab | What it shows |
|-----|---------------|
| **✦ viz** | Expression tree for any math input — nodes colored by EML / EDL / EXL routing. |
| **sin↗** | sin(x) Taylor accuracy chart, 2–20 terms. BEST vs EML node count at every precision level. |
| **⚡ demo** | Live JS GELU FFN timing (EML vs BEST) + Python experiment_10 numbers side by side. |
| **Calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with per-operation node breakdown. |
| **Opt** | Paste Python/NumPy/PyTorch code — get a BEST-rewritten version + savings estimate. When `python api/main.py` is running locally, uses real AST rewriting via `best_optimize()`. |
| **Board** | Challenge leaderboard — open problems in EML construction (sin, cos, π). |

---

## Open challenges

No known closed-form EML construction exists for:

- **sin x**, **cos x** — 862,116 trees (N≤8) searched, zero hits; Taylor via BEST works numerically
- **π** — no construction as a closed EML expression from terminal `{1}`
- **i** (√−1) — open under strict principal-branch grammar

Pull requests welcome. Crack one and open an issue — it's publishable.

---

## Repository structure

```
monogate/
├── python/          # pip install monogate  — core, torch_ops, network, optimize
├── lib/             # npm install monogate  — JS/Node library
├── explorer/        # monogate.dev          — Vite/React browser app
├── api/             # Python FastAPI server — powers Opt tab in local mode
└── challenge/       # Challenge board backend
```

## License

MIT. The underlying mathematics is CC BY 4.0 per the original paper.
