# monogate

> A single binary operator that generates all elementary functions.

```
eml(x, y) = exp(x) − ln(y)
```

From this one operator and the constant `1`, every elementary arithmetic function can be constructed as a pure expression tree. Implementation of:

> **"All elementary functions from a single operator"**
> Andrzej Odrzywołek, Jagiellonian University
> [arXiv:2603.21852v2](https://arxiv.org/abs/2603.21852) · CC BY 4.0

Live explorer: **https://monogate.dev** (or your deployed URL)

---

## Install

**JavaScript / Node**
```bash
npm install monogate
```

**Python**
```bash
pip install monogate            # core only (no dependencies)
pip install "monogate[torch]"   # + PyTorch differentiable ops + EMLTree / EMLNetwork
```

## Usage

```js
import { op, exp, ln, add, mul, pow, E, ZERO } from "monogate";

// The core operator
op(1, 1);        // e        (exp(1) − ln(1))
op(1, op(op(1,1), 1));  // 0   (e − e = 0)

// Derived functions — all built from eml + 1
exp(3);          // e³
ln(Math.E);      // 1
add(2, 3);       // 5
mul(4, 5);       // 20
pow(2, 10);      // 1024
```

## API

All functions are pure and stateless. Domain constraints are noted — violating them produces `NaN` or `±Infinity`.

### Core

| Export | Formula | Nodes | Depth |
|--------|---------|-------|-------|
| `op(x, y)` | `exp(x) − ln(y)` | — | — |
| `E` | `op(1,1)` | 1 | 1 |
| `ZERO` | `op(1, op(op(1,1), 1))` | 3 | 3 |
| `NEG_ONE` | `op(ZERO, op(2,1))` | 5 | 4 |

### Elementary functions

| Export | Math | Domain | Nodes | Depth |
|--------|------|--------|-------|-------|
| `exp(x)` | eˣ | ℝ | 1 | 1 |
| `ln(x)` | ln x | x > 0 | 3 | 3 |
| `sub(x, y)` | x − y | x > 0 | 5 | 4 |
| `neg(y)` | −y | ℝ (two-regime) | 9 | 5 |
| `add(x, y)` | x + y | ℝ | 11 | 6 |
| `mul(x, y)` | x × y | x,y > 0 | 13 | 7 |
| `div(x, y)` | x / y | x,y > 0 | 15 | 8 |
| `pow(x, n)` | xⁿ | x > 0 | 15 | 8 |
| `recip(x)` | 1/x | x > 0 | 5 | 4 |

The **depth** ranking of elementary functions by EML tree depth is new to mathematics.

### `IDENTITIES`

An array of `{ name, emlForm, nodes, depth, status }` records — useful for building explorers or documentation.

## Operator family

EML is not the only universal operator of this form. We have characterised a
family of related gates and compared them systematically:

| Operator | Gate | Constant | Complete? | Best operation |
|----------|------|----------|-----------|----------------|
| **EML** | `exp(x) − ln(y)` | 1 | Yes | sub (5n), add (11n) |
| **EDL** | `exp(x) / ln(y)` | e | Yes | div (1n), mul (7n), recip (2n) |
| **EXL** | `exp(x) × ln(y)` | e | No  | ln (1n), pow (3n) |
| EAL | `exp(x) + ln(y)` | 1 | No  | exp (1n) |
| EMN | `ln(y) − exp(x)` | 1 | No  | — |

**EML and EDL are the only complete operators** — they can each build all
elementary arithmetic. EXL is incomplete (cannot add arbitrary reals) but gives
the cheapest ln and pow.

### BEST: optimal per-operation routing

`BEST` is a pre-built hybrid that picks the cheapest known operator for each
operation:

| Operation | Routed to | Nodes | EML baseline | Saving |
|-----------|-----------|-------|--------------|--------|
| exp | EML | 1 | 1 | same |
| ln | EXL | 1 | 3 | −2 |
| pow | EXL | 3 | 15 | −12 |
| mul | EDL | 7 | 13 | −6 |
| div | EDL | 1 | 15 | −14 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | same |
| add | EML | 11 | 11 | same |

Total routing overhead: **37 nodes** vs 77 nodes all-EML — **52% fewer nodes**.

```python
from monogate import BEST
BEST.pow(2.0, 10.0)   # 1024.0  (uses pow_exl, 3 nodes)
BEST.div(6.0, 2.0)    # 3.0     (uses div_edl, 1 node)
BEST.add(3.0, 4.0)    # 7.0     (uses add_eml, 11 nodes)
BEST.benchmark()      # prints node-count table + accuracy checks
```

### sin(x) via Taylor series

Using BEST routing, sin(x) = x − x³/3! + x⁵/5! − … can be computed with
**63 nodes** at 8 terms (max error 7.7 × 10⁻⁷) vs **245 nodes** all-EML — a
74% saving. Machine precision (~6.5 × 10⁻¹⁵) is reached at 13 terms (108 nodes
BEST vs 420 nodes EML-only).

The additive steps (sub_eml / add_eml) are the irreducible EML-only cost — no
cousin operator currently supports arbitrary a ± b. This makes EML structurally
essential even when other operators are cheaper for individual operations.

## Open challenges

These functions have no known **closed-form EML construction** (exact formula, not Taylor series):

- **sin x** — Taylor via BEST routing works numerically; exact closed-form unknown
- **cos x** — same status as sin x
- **π** — no construction as a closed EML expression
- **i** (√−1) — open under strict principal-branch grammar. Under the extended-reals convention (`ln(0) = −∞`), i is constructible from `{1}` alone in K=75 nodes ([pveierland/eml-eval](https://github.com/pveierland/eml-eval)). These are different grammars, not contradictory results.

Pull requests welcome. If you crack one, open an issue — it's publishable.

## How it works

The grammar is just two production rules:

```
S → 1
S → eml(S, S)
```

Any expression built from this grammar computes some value. The paper proves that the specific compositions above equal the named functions exactly (not approximately). Floating-point errors are at machine epsilon (`< 1e-13`).

The `neg` function uses a two-regime construction to avoid overflow:
- **y ≤ 0**: tower formula via `exp(eʸ)` — stable because `eʸ ≤ 1`
- **y > 0**: shift formula — computes `exp(y+1)` instead of a tower

## License

MIT — see [LICENSE](./LICENSE). The underlying mathematics is CC BY 4.0 per the original paper.
