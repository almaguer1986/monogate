# monogate

**monogate** implements EML arithmetic — a formal system where every elementary function is a finite binary tree of identical gates — and routes each operation to the cheapest known operator family, cutting node counts by 20–74% and delivering measurable wall-clock speedup for pow/ln-heavy workloads.

```
eml(x, y) = exp(x) − ln(y)       ← the one gate
```

From this operator and the constant `1`, every elementary arithmetic function is constructible as an exact expression tree. Implementation of:

> **"All elementary functions from a single operator"**
> Andrzej Odrzywołek, Jagiellonian University
> [arXiv:2603.21852v2](https://arxiv.org/abs/2603.21852) · CC BY 4.0

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

## Real Speedups

Node-count savings translate to wall-clock speedup only above a threshold. Three experiments measured this directly (Python, CPU):

| Workload | Activation | Nodes (EML) | Nodes (BEST) | Savings | Speedup |
|----------|-----------|-------------|-------------|---------|---------|
| TinyMLP, sin (exp_09) | sin(x) 8-term Taylor | 245 | 63 | **74%** | **2.8–3.1×** |
| Batch poly eval (exp_11) | x⁴+x³+x² | 67 | 31 | **54%** | **2.1×** |
| Transformer FFN (exp_10) | tanh-GELU | 17 | 14 | 18% | 0.93× |

Linear model (R²=0.9992): `speedup ≈ 0.033 × savings_pct + 0.32`

**Crossover at ~20% node reduction.** GELU at 18% falls below the threshold — Python call overhead dominates. sin/cos at 74% give a solid 2.8–3.1× gain.

For reference: native `torch.sin` is ~440× faster than any EML variant. These benchmarks are relevant for symbolic arithmetic, EML tree evaluation, and differentiable programs that use EML as a numeric substrate.

---

## Operator family

| Operator | Gate | Constant | Complete? | Cheapest operations |
|----------|------|----------|-----------|---------------------|
| **EML** | `exp(x) − ln(y)` | 1 | **Yes** | sub (5n), add (11n) |
| **EDL** | `exp(x) / ln(y)` | e | **Yes** | div (1n), recip (2n), mul (7n) |
| **EXL** | `exp(x) × ln(y)` | e | No | ln (1n), pow (3n) |
| EAL | `exp(x) + ln(y)` | 1 | No | — |
| EMN | `ln(y) − exp(x)` | 1 | No | — |

EML and EDL are the only complete operators. EXL is incomplete (cannot add arbitrary reals) but is the cheapest for `ln` and `pow`.

### BEST: optimal per-operation routing

`BEST` dispatches each primitive to the cheapest known operator:

| Operation | Operator | BEST nodes | EML baseline | Saving |
|-----------|----------|-----------|--------------|--------|
| exp | EML | 1 | 1 | — |
| ln | EXL | 1 | 3 | −2 |
| pow | EXL | 3 | 15 | −12 |
| mul | EDL | 7 | 13 | −6 |
| div | EDL | 1 | 15 | −14 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | — |
| add | EML | 11 | 11 | — |

Total: **37 nodes** vs 77 all-EML — 52% fewer. The add/sub steps stay EML; no other operator currently supports arbitrary a ± b.

---

## When to use BEST

Use BEST routing when your workload:

- Contains activations with ≥21% node savings (sin, cos, polynomial expressions)
- Is dominated by `pow`, `ln`, `mul`, or `div`
- Builds deep expression trees where overhead amortises across many nodes
- Is doing symbolic regression or interpretable expression search

Do not expect wall-clock gains when:
- The primary operations are `add` or `sub` (no savings — EML-only)
- Total node reduction is under ~20% (GELU at 18% is a concrete example)
- You are using native PyTorch/NumPy (those are already optimised at the C level)

---

## Quick start

**Python**
```python
from monogate import op, E, ZERO, add_eml, mul_eml, pow_eml
from monogate import BEST

op(1, 1)             # e
add_eml(2, 3)        # 5.0
pow_eml(2, 8)        # 256.0

BEST.pow(2.0, 10.0)  # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)   # 3.0     (EDL, 1 node  vs 15)
BEST.add(3.0, 4.0)   # 7.0     (EML, 11 nodes — irreducible)
BEST.benchmark()     # full node-count + accuracy report
```

**JavaScript**
```js
import { op, exp, ln, add, mul, pow, BEST } from "monogate";

op(1, 1);              // e
add(2, 3);             // 5
BEST.pow(2, 10);       // 1024  (EXL, 3 nodes)
BEST.div(6, 2);        // 3     (EDL, 1 node)
```

---

## Explorer (monogate.dev)

| Tab | Description |
|-----|-------------|
| **✦ viz** | Expression tree for any math input, nodes colored by EML / EDL / EXL routing. Click subtrees to highlight. |
| **sin↗** | sin(x) Taylor accuracy chart, 2–20 terms. BEST vs EML node count at every precision level. |
| **⚡ demo** | Live JS GELU FFN timing (EML vs BEST) + Python experiment_10 numbers side by side. |
| **Calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with per-operation node breakdown. |
| **Opt** | Paste Python/NumPy/PyTorch code and get a BEST-rewritten version with node savings estimate. |
| **Board** | Challenge leaderboard — open problems in EML construction (sin, cos, π). Submit a construction, get credited. |

---

## Open challenges

These have no known **closed-form EML construction** (exact tree, not Taylor series):

- **sin x**, **cos x** — Taylor via BEST works numerically; exact closed-form unknown
- **π** — no construction as a closed EML expression
- **i** (√−1) — open under strict principal-branch grammar; constructible under the extended-reals convention (K=75 nodes, [pveierland/eml-eval](https://github.com/pveierland/eml-eval)) — different grammars, not contradictory

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
