# monogate

monogate finds the most compact symbolic representation of elementary functions using a hybrid operator router (BEST).

```
eml(x, y) = exp(x) − ln(y)       ← the one gate
```

From this single binary operator and the constant `1`, every elementary function is an exact expression tree — no look-up tables, no approximation for the core identities. BEST routing then dispatches each primitive to whichever of three operator families (EML, EDL, EXL) uses the fewest nodes.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).  
Live explorer: **[monogate.dev](https://monogate.dev)**

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

## Real numbers

Node-count savings translate to wall-clock speedup only above a threshold (~20% reduction). Three experiments measured this directly on Python scalars:

| Workload | Operation | Nodes (EML) | Nodes (BEST) | Savings | Speedup |
|----------|-----------|-------------|-------------|---------|---------|
| TinyMLP, sin (exp_09, exp_12) | sin Taylor 8-term | 245 | 63 | **74%** | **2.8–3.4×** |
| Batch poly eval (exp_11) | x⁴+x³+x² | 67 | 31 | **54%** | **2.1×** |
| Transformer FFN (exp_10) | tanh-GELU | 17 | 14 | 18% | 0.93× |

Linear model (R²=0.9992): `speedup ≈ 0.033 × savings_pct + 0.32`

GELU at 18% falls just below the crossover — Python call overhead dominates. sin/cos at 74% deliver a solid 2.8–3.4× gain within the EML substrate.

---

## When to use it

BEST routing pays off when your workload:

- Does symbolic regression or interpretable expression search
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Evaluates the same expression repeatedly across many inputs
- Needs human-readable formula output from a differentiable tree
- Is building or analyzing EML expression trees

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

## Quick start

**Python**
```python
from monogate import BEST, pow_eml, div_eml

# BEST routing — cheapest gate per operation
BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs 15)
BEST.ln(2.718)        # ~1.0    (EXL, 1 node  vs 3)
BEST.add(3.0, 4.0)    # 7.0     (EML, 11 nodes — irreducible)

# Symbolic regression — fit a tree to approximate f(x) = x²
# See python/examples/symbolic_regression.py
```

**JavaScript**
```js
import { BEST } from "monogate";

BEST.pow(2, 10);   // 1024  (EXL, 3 nodes)
BEST.div(6, 2);    // 3     (EDL, 1 node)
```

---

## Explorer (monogate.dev)

| Tab | What it shows |
|-----|---------------|
| **✦ viz** | Expression tree for any math input — nodes colored by EML / EDL / EXL routing. Click subtrees to highlight. |
| **sin↗** | sin(x) Taylor accuracy chart, 2–20 terms. BEST vs EML node count at every precision level. |
| **⚡ demo** | Live JS GELU FFN timing (EML vs BEST) + Python experiment_10 numbers side by side. |
| **Calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with per-operation node breakdown. |
| **Opt** | Paste Python/NumPy/PyTorch code — get a BEST-rewritten version with node savings estimate. |
| **Board** | Challenge leaderboard — open problems in EML construction (sin, cos, π). Submit and get credited. |

---

## Open challenges

No known closed-form EML construction exists for:

- **sin x**, **cos x** — Taylor via BEST works numerically; exact closed-form unknown
- **π** — no construction as a closed EML expression
- **i** (√−1) — open under strict principal-branch grammar

Pull requests welcome. Crack one and open an issue — it's publishable.

---

## Repository structure

```
monogate/
├── python/          # pip install monogate  — core, torch_ops, network, optimize
├── lib/             # npm install monogate  — JS/Node library
├── explorer/        # monogate.dev          — Vite/React browser app
└── challenge/       # Challenge board backend
```

## License

MIT. The underlying mathematics is CC BY 4.0 per the original paper.
