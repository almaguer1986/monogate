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

## `monogate/cost` — Pfaffian cost analysis

Sub-path import (added in 1.2.0). Analyzes a symbolic expression and
returns its Pfaffian profile: chain order, EML routing depth, structural
overhead, oscillation/composite/fusion corrections, and a canonical
cost-class fingerprint string.

```js
import { analyze, parse, distance } from 'monogate/cost';

analyze('exp(sin(x))');
// { pfaffian_r: 3, max_path_r: 3, eml_depth: 4,
//   structural_overhead: 0,
//   corrections: { c_osc: 1, c_composite: 0, delta_fused: 0 },
//   predicted_depth: 4, is_pfaffian_not_eml: false,
//   cost_class: 'p3-d4-w3-c1' }

analyze('1/(1+exp(-x))').cost_class;   // 'p1-d2-w1-c0' — sigmoid, fused
analyze('log(1+exp(x))').cost_class;   // 'p2-d1-w2-c-1' — softplus, fused
analyze('x*(1+erf(x/sqrt(2)))/2');     // GELU exact, is_pfaffian_not_eml=true
```

The cost-class string follows the Python `eml-cost` convention:
`p<pfaffian_r>-d<eml_depth>-w<max_path_r>-c<correction_sum>` where
`correction_sum = c_osc + c_composite − delta_fused`. All 32
cross-checked test cases produce byte-identical fingerprints to the
Python `eml-cost` package.

Distance metric for clustering / equivalence-class lookup:

```js
import { analyze, distance, compare } from 'monogate/cost';

const a = analyze('1/(1+exp(-x))');                // sigmoid
const b = analyze('exp(x)/(1+exp(x))');            // also sigmoid
distance(a, b);                                    // weighted L2
compare(a, b);                                     // per-axis deltas
```

Reference: [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) +
Khovanskii (1991) Pfaffian fewnomials.

## Open challenges

These functions have no known EML construction:

- **sin x** — no construction found
- **cos x** — no construction found
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
