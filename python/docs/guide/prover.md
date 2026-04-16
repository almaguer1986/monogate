# Neurosymbolic Theorem Prover

The `monogate.prover` module implements a multi-tier neurosymbolic theorem
prover that can verify mathematical identities of the form `f(x) = g(x)`.

## What is a Neurosymbolic Proof in EML?

A **neurosymbolic proof** combines stochastic search (MCTS) with symbolic
verification (SymPy). The key insight is that any elementary function can
be expressed as an EML tree — and if we can *find* the EML tree that equals
a target function, we have a constructive proof witness.

The three-tier proof hierarchy works as follows:

```
Identity  f(x) = g(x)
     │
     ├── Tier 1 (Numerical)    max|f−g| < 1e-8 on 500 probe points
     ├── Tier 2 (Exact/SymPy)  simplify(f_expr − g_expr) == 0
     ├── Tier 3 (Certified)    interval arithmetic over 20 sub-intervals
     └── Tier 4 (EML Witness)  MCTS discovers T ≈ f; simplify(T − g) == 0
```

**Why neurosymbolic?** MCTS is the *neural* component (stochastic exploration
of the EML expression space), and SymPy provides the *symbolic* verification.
The two work together: MCTS finds candidate EML trees, and SymPy confirms
them algebraically. An EML tree T such that `simplify(to_sympy(T) - g) == 0`
is called a **proof witness** for the identity `f = g`.

## Quick Start

```python
from monogate.prover import EMLProver

prover = EMLProver(verbose=True)

# Prove a simple exponential identity
r = prover.prove("exp(x) * exp(-x) == 1")
print(r.status)       # 'proved_exact'
print(r.confidence)   # 1.0
print(r.latex_proof)  # LaTeX proof string

# Prove a trigonometric identity
r = prover.prove("sin(x)**2 + cos(x)**2 == 1")
print(r.status)       # 'proved_exact' or 'proved_numerical'
```

## Proof Modes

### Exact Proof (`proved_exact`)

Uses SymPy's `simplify` to verify `LHS − RHS == 0` symbolically.

```python
r = prover.prove("cosh(x)**2 - sinh(x)**2 == 1")
assert r.status == "proved_exact"
assert r.confidence == 1.0
assert r.sympy_simplification == "0"
```

Confidence: **1.0** (no floating-point involved).

### Numerical Proof (`proved_numerical`)

Evaluates `|f(x) − g(x)|` at 500 probe points using the `math` module.
If max residual < 1e-8, the identity is "proved numerically".

```python
r = prover.prove("cos(x + 1) == cos(x)*cos(1) - sin(x)*sin(1)")
assert r.status == "proved_numerical"
assert r.confidence == 0.9
```

Confidence: **0.9** (floating-point; cannot rule out edge cases).

### Certified Proof (`proved_certified`)

Splits the domain into 20 sub-intervals and evaluates `|f − g|` at each
endpoint. If max residual < 1e-6, the proof is "certified".

Confidence: **0.95** (tighter than purely numerical but not symbolic).

### EML Witness Proof (`proved_witness`)

MCTS searches for an EML tree T such that T(x) ≈ f(x). If found, SymPy
verifies `simplify(to_sympy(T) − rhs_expr) == 0`. This gives a constructive
proof witness — an EML expression that *is* the left-hand side.

```python
r = prover.prove(
    "exp(x) * exp(-x) == 1",
    n_simulations=3000,
    max_nodes=8,
)
if r.status == "proved_witness":
    print(f"Witness: {r.lhs_formula}")
    print(f"Nodes:   {r.node_count}")
```

Confidence: **1.0** (SymPy verified).

### Inconclusive / Failed

If none of the above strategies succeed:

- `inconclusive`: residual is small (< 1e-4) but above proof threshold
- `failed`: large residual or unparseable identity

```python
# False identity — should fail
r = prover.prove("sin(x) == 2")
assert r.status == "failed"

# Malformed identity — should fail
r = prover.prove("sin(x) + cos(x)")  # no '=='
assert r.status == "failed"
```

## Identity Catalog

The `monogate.identities` module provides a rich catalog of 50+ identities:

```python
from monogate.identities import (
    ALL_IDENTITIES,
    TRIG_IDENTITIES,
    HYPERBOLIC_IDENTITIES,
    EXPONENTIAL_IDENTITIES,
    SPECIAL_IDENTITIES,
    PHYSICS_IDENTITIES,
    EML_IDENTITIES,
    OPEN_IDENTITIES,
    get_by_difficulty,
    get_by_category,
)

# Browse by difficulty
trivials = get_by_difficulty("trivial")
easy = get_by_difficulty("easy")
hard = get_by_difficulty("hard")

# Browse by category
trig = get_by_category("trigonometric")
physics = get_by_category("physics")

# Each Identity has full metadata
for ident in TRIG_IDENTITIES[:3]:
    print(f"{ident.name}: {ident.expression}")
    print(f"  LaTeX:  {ident.latex}")
    print(f"  Domain: {ident.domain}")
    print(f"  Difficulty: {ident.difficulty}")
```

### Identity Categories

| Category | Count | Examples |
|----------|-------|---------|
| `trigonometric` | 17 | Pythagorean, double-angle, power reduction |
| `hyperbolic` | 12 | cosh²−sinh²=1, tanh definition |
| `exponential` | 12 | exp(x)exp(−x)=1, log(exp(x))=x |
| `special` | 12 | Gamma recurrence, erf symmetry |
| `physics` | 7 | Schrodinger unitarity, heat kernel |
| `eml` | 6 | exp as eml(x,1), negation via log |
| `open` | 5 | Deep sin representation, phantom attractor |

### Difficulty Levels

- `trivial`: Direct evaluation (exp(0)=1, log(1)=0)
- `easy`: Single-step algebra (Pythagorean, double-angle)
- `medium`: Multi-step simplification (power reduction, triple angle)
- `hard`: Requires deep symbolic or numerical proof
- `open`: Currently unproved or requires very deep EML trees

## API Reference

### `EMLProver`

```python
class EMLProver:
    def __init__(self, verbose: bool = False, n_probe: int = 500)
    
    def prove(
        self,
        identity: str,
        max_nodes: int = 10,
        n_simulations: int = 3000,
        timeout: float = 60.0,
        domain: tuple[float, float] = (-π, π),
        seed: int = 42,
    ) -> ProofResult
    
    def prove_batch(
        self,
        identities: list[str],
        **kwargs,
    ) -> list[ProofResult]
    
    def benchmark(
        self,
        catalog: list | None = None,
        n_simulations: int = 1000,
        timeout: float = 30.0,
        **kwargs,
    ) -> BenchmarkReport
```

**Parameters:**

- `verbose`: Print progress messages during proving.
- `n_probe`: Number of probe points for numerical checks (default 500).
- `identity`: Identity string, e.g. `"sin(x)**2 + cos(x)**2 == 1"`.
- `max_nodes`: Maximum EML tree nodes for MCTS witness search.
- `n_simulations`: MCTS simulation count (higher = more thorough but slower).
- `timeout`: Soft wall-clock limit per identity.
- `domain`: `(lo, hi)` interval for testing.
- `seed`: Random seed for reproducibility.

### `ProofResult`

```python
@dataclass(frozen=True)
class ProofResult:
    identity_str: str          # original identity string
    status: str                # 'proved_exact' | 'proved_certified' | ...
    verification_method: str   # 'sympy' | 'interval' | 'numerical' | 'eml_witness' | ...
    confidence: float          # 0.0–1.0
    max_residual: float        # max |lhs(x)−rhs(x)|
    n_test_points: int         # number of probe points evaluated
    elapsed_s: float           # wall-clock seconds
    lhs_tree: dict | None      # EML tree for LHS (if MCTS found one)
    rhs_tree: dict | None      # EML tree for RHS (if MCTS found one)
    witness_tree: dict | None  # EML proof witness
    node_count: int            # nodes in witness or LHS tree
    lhs_formula: str | None    # human-readable EML formula
    latex_proof: str | None    # LaTeX proof block
    sympy_simplification: str | None  # SymPy simplify() result
    notes: list[str]           # proof steps / observations
    
    def proved(self) -> bool   # True if status starts with 'proved'
```

### `BenchmarkReport`

```python
@dataclass
class BenchmarkReport:
    results: list[ProofResult]
    n_total: int
    n_proved: int
    n_exact: int
    n_numerical: int
    n_failed: int
    success_rate: float
    mean_elapsed_s: float
    mean_nodes: float
    
    def summary(self) -> str   # formatted ASCII table
    def to_json(self) -> dict  # JSON-serialisable dict
```

### `Identity`

```python
@dataclass(frozen=True)
class Identity:
    name: str
    expression: str        # parseable '==' identity string
    latex: str             # LaTeX math
    category: str          # e.g. 'trigonometric'
    domain: tuple          # (lo, hi)
    difficulty: str        # 'trivial'|'easy'|'medium'|'hard'|'open'
    notes: str = ""
    expected_method: str = "exact"  # 'exact'|'numerical'|'unknown'
```

## LaTeX Export

Every `ProofResult` carries a `latex_proof` field with a self-contained
LaTeX proof block:

```python
r = prover.prove("exp(x) * exp(-x) == 1")

with open("proof.tex", "w", encoding="utf-8") as f:
    f.write(r"\documentclass{article}\n")
    f.write(r"\usepackage{amsmath, amsthm}\n")
    f.write(r"\newtheorem{theorem}{Theorem}\n")
    f.write(r"\begin{document}\n")
    f.write(r.latex_proof or "% proof unavailable")
    f.write(r"\end{document}\n")
```

The generated LaTeX uses `\begin{proof}...\end{proof}` with the identity,
method, and SymPy result embedded.

## Batch Benchmarking

Run the full benchmark over all easy identities:

```python
from monogate.identities import get_by_difficulty
from monogate.prover import EMLProver

prover = EMLProver(n_probe=200)
catalog = get_by_difficulty("easy")

report = prover.benchmark(
    catalog=catalog,
    n_simulations=1000,
    timeout=30.0,
)

print(report.summary())
# ════════════════════════════════════════════════════════════════════════
#   EML Theorem Prover Benchmark  —  N identities
# ...
#   Proved:       K/N  (X%)
#   Exact:        ...
#   Numerical:    ...
# ════════════════════════════════════════════════════════════════════════

# Export results
import json
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(report.to_json(), f, indent=2)
```

## Limitations and Honest Failure Analysis

### SymPy is Not Complete

SymPy's `simplify` cannot prove every true identity. Some identities require:
- Trigonometric-specific simplifiers (`trigsimp`, `expand_trig`)
- Manual substitution chains
- Non-trivial variable changes

For such cases, the prover falls back to numerical verification.

### MCTS Has Depth Limits

The witness search explores EML trees up to `max_nodes` nodes. Functions like
`sin(x)` and `cos(x)` cannot be represented by *any finite* EML tree in exact
form — they require infinite-depth trees (power series). The prover is honest
about this: it reports `inconclusive` or `failed`, not a false positive.

### Numerical Proofs Are Not Formal

A `proved_numerical` status means max|f−g| < 1e-8 on 500 points — this is
strong empirical evidence but not a mathematical proof. For formal guarantees,
use `proved_exact` (SymPy) or `proved_witness` (EML witness + SymPy).

### Domain Restrictions

Some identities only hold on restricted domains:
- `exp(log(x)) == x` requires `x > 0`
- `log(x**2) == 2*log(x)` requires `x > 0`
- `tan(x)` identities require `cos(x) ≠ 0`

Always set the `domain` parameter appropriately.

## Advanced: Phantom Attractor Robustness

The EML witness search is designed to escape the *phantom attractor* — a
known failure mode of gradient-based EML optimization where search converges
to `eml(0, 1) = 1 − 0 = 1` regardless of the target. MCTS avoids this by
exploring tree structures rather than just parameters.

```python
# Identity that trips gradient-based search
r = prover.prove(
    "exp(x) * exp(-x) == 1",
    n_simulations=5000,
    max_nodes=6,
)
# MCTS should find eml(x, eml(x, 1)) as a witness
```

## Integration with Other monogate Modules

```python
# Use with sympy_bridge
from monogate.sympy_bridge import to_sympy, verify_identity

# Manual verification using sympy_bridge
tree = {"op": "eml", "left": {"op": "leaf", "val": "x"},
                      "right": {"op": "leaf", "val": 1.0}}
expr = to_sympy(tree)  # exp(x) - log(1) = exp(x)

# Use with interval arithmetic
from monogate.interval import eval_interval, Interval
iv = eval_interval(tree, Interval(-1.0, 1.0))
print(f"exp(x) over [-1,1]: {iv}")

# Use with MCTS directly
from monogate.search.mcts import mcts_search
result = mcts_search(lambda x: x**2, depth=4, n_simulations=1000)
```

## References

- monogate arXiv paper: [arXiv:2603.21852](https://arxiv.org/abs/2603.21852)
- SymPy documentation: [sympy.org](https://www.sympy.org)
- MCTS for symbolic regression: see `guide/mcts.md`
- Interval arithmetic: see `monogate.interval`
