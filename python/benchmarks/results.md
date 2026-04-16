# Symbolic Regression Benchmark — monogate vs baselines

Comparison of EML/BEST + MCTS/Beam Search against PySR and gplearn on 5 regression targets.  All methods evaluated on 50 probe points in [-3, 3] with fixed budgets.

## MSE Comparison

| Method | sin(x) | exp(-x^2) | 1/(1+x^2) | x*sin(x) | GELU(x) |
|--------|:------:|:------:|:------:|:------:|:------:|
| EML Beam (d=6, w=200) | 3.480e-01 | 1.293e-01 | 1.024e-01 | 3.841e-01 | 2.772e-01 |
| EML MCTS (d=6, 10k sims) | 5.131e-01 | 2.047e-01 | 4.332e-01 | 3.841e-01 | 1.118e+00 |

## Wall-clock Time (seconds)

| Method | sin(x) | exp(-x^2) | 1/(1+x^2) | x*sin(x) | GELU(x) |
|--------|:------:|:------:|:------:|:------:|:------:|
| EML Beam (d=6, w=200) | 0.04s | 0.04s | 0.05s | 0.03s | 0.03s |
| EML MCTS (d=6, 10k sims) | 0.13s | 0.13s | 0.13s | 0.14s | 0.13s |

## Best Formulas

- **EML MCTS (d=6, 10k sims)** on `sin(x)`: `eml(1.0, eml(eml(1.0, 1.0), 1.0))`
- **EML Beam (d=6, w=200)** on `sin(x)`: `eml(x, eml(eml(x, 1.0), eml(x, 1.0)))`
- **EML MCTS (d=6, 10k sims)** on `exp(-x^2)`: `eml(1.0, eml(eml(1.0, 1.0), 1.0))`
- **EML Beam (d=6, w=200)** on `exp(-x^2)`: `eml(1.0, eml(eml(1.0, 1.0), eml(eml(1.0, 1.0), 1.0)))`
- **EML MCTS (d=6, 10k sims)** on `1/(1+x^2)`: `1.0`
- **EML Beam (d=6, w=200)** on `1/(1+x^2)`: `eml(1.0, eml(eml(1.0, eml(1.0, eml(1.0, 1.0))), 1.0))`
- **EML MCTS (d=6, 10k sims)** on `x*sin(x)`: `1.0`
- **EML Beam (d=6, w=200)** on `x*sin(x)`: `eml(x, eml(eml(x, eml(1.0, 1.0)), 1.0))`
- **EML MCTS (d=6, 10k sims)** on `GELU(x)`: `1.0`
- **EML Beam (d=6, w=200)** on `GELU(x)`: `eml(1.0, eml(eml(1.0, eml(x, eml(x, 1.0))), 1.0))`

## Notes

- EML MCTS and Beam Search are constrained to the EML grammar (`eml(a,b) = exp(a) - ln(b)` with terminals `{1, x}`).  They cannot produce trigonometric or general polynomial primitives, so they are systematically disadvantaged on `sin(x)` and `x*sin(x)`.
- The Infinite Zeros Barrier proves no finite EML tree can exactly represent `sin(x)` for all real x; 40.2M trees searched (N<=10), zero candidates.
- PySR and gplearn have access to `sin`, `cos`, `exp`, `log` primitives; EML methods do not.  Fair comparison requires restricting baselines to `{+, -, *, /}` only.
