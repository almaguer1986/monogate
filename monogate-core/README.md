# monogate-core

Native Rust extension for [monogate](https://pypi.org/project/monogate/) — a
Python library for **EML (Exp-Minus-Log) arithmetic**: `eml(a, b) = exp(a) - ln(b)`.

This crate provides compiled kernels that Python can call via
[PyO3](https://pyo3.rs), targeting a **50–200× speedup** over the Python/PyTorch
`FusedEMLActivation` for large batches.

---

## What's inside

| Module | Purpose |
|--------|---------|
| `evaluator` | Iterative bottom-up EML/BEST tree evaluation; rayon-parallel for batches ≥ 1 000 |
| `sin_search` | Bitmask-encoded tree search helpers for the sin(x) barrier research |
| `lib` (PyO3) | Python bindings: `eval_eml_batch`, `eval_best_batch`, `benchmark_rust` |

### Operators

- **EML** — all nodes use `eml(a, b) = exp(a) - ln(softplus(b))`
- **BEST** — hybrid routing: inner nodes use `exl(a, b) = exp(a) * ln(softplus(b))`, root uses EML

---

## Build

### Prerequisites

- [Rust](https://rustup.rs/) (stable, 1.75+)
- Python 3.10+
- [maturin](https://github.com/PyO3/maturin)

```bash
pip install maturin
```

### Development build (fast, unoptimised)

```bash
cd monogate-core
maturin develop
```

### Release build (full optimisations; recommended for benchmarking)

```bash
maturin develop --release
```

### Wheel for distribution

```bash
maturin build --release
# wheel appears in target/wheels/
```

---

## Usage from Python

```python
import numpy as np
import monogate_core

# depth=2 EML tree: 4 leaves
leaf_w = np.array([0.05, 0.05, 0.05, 0.05])
leaf_b = np.array([1.0,  1.0,  1.0,  1.0])
x      = np.linspace(-2.0, 2.0, 100_000)

# EML evaluation
out = monogate_core.eval_eml_batch(leaf_w, leaf_b, x, depth=2, operator="EML")

# BEST routing
out_best = monogate_core.eval_best_batch(leaf_w, leaf_b, x, depth=2)

# Throughput benchmark
mps = monogate_core.benchmark_rust(n=1_000_000, depth=2)
print(f"Rust throughput: {mps:.0f} M eval/sec")

# Sin-search helpers
result = monogate_core.eval_tree_assignment(0b0101, n_leaves=4, probe_x=0.5)
passes = monogate_core.check_parity_bits(0b0101, n_leaves=4)
```

### Drop-in wrapper with PyTorch fallback

```python
# Install monogate-core, then:
from monogate.fused_rust import RustFusedLayer, RUST_AVAILABLE

if RUST_AVAILABLE:
    layer = RustFusedLayer(depth=2, operator="EML")
else:
    # Falls back to FusedEMLActivation (PyTorch)
    from monogate.compile import FusedEMLLayer
    layer = FusedEMLLayer(1, 1, depth=2)
```

---

## Running tests

```bash
cargo test
```

## Running benchmarks

```bash
cargo bench
# HTML reports: target/criterion/index.html
```

---

## Architecture notes

- **No `unsafe` blocks** — fully safe Rust.
- **No Python recursion** — the tree traversal is a plain `for` loop over levels.
- **Rayon parallelism** — engaged automatically when `batch_size >= 1_000`.
  Set `RAYON_NUM_THREADS=N` to control thread count.
- **softplus safety** — `ln(softplus(b))` is used instead of `ln(b)` to match
  Python's `FusedEMLActivation` and avoid domain errors for negative inputs.

---

## Relationship to monogate Python package

```
monogate/
├── python/monogate/          # Python library (PyPI: monogate)
│   ├── compile/fused.py      # FusedEMLActivation (PyTorch)
│   └── fused_rust.py         # ← wrapper that calls this crate
└── monogate-core/            # ← this Rust crate
    ├── src/lib.rs            # PyO3 module
    ├── src/evaluator.rs      # Core eval logic
    └── src/sin_search.rs     # Sin-barrier search helpers
```
