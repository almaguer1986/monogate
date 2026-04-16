# Complex EML

## The Infinite Zeros Barrier — and how to bypass it

The **Infinite Zeros Barrier** is a theorem established by the monogate exhaustive search (N ≤ 10):

> **Theorem.** No finite real-valued EML expression tree can equal sin(x) for all real x.

**Proof sketch.** Any finite EML tree is a composition of `exp` and `log` — a real-analytic function with *finitely many* zeros on any bounded interval. But sin(x) has *infinitely many* zeros (x = kπ for all integers k). No real-analytic function with finitely many zeros can equal sin on all of ℝ.

**Implications:**
- Gradient descent on EMLTree targeting sin(x) is doomed to fail (or find a local optimum)
- The phantom attractor (3.1696) is where many seeds end up
- No amount of depth or node count fixes this for real-valued trees

---

## The Euler bypass

Moving to the *complex* domain removes the barrier:

```
eml(ix, 1) = exp(ix) - ln(1) = exp(ix) = cos(x) + i·sin(x)
```

This is **Euler's formula** expressed as a single EML node. Taking the imaginary part:

```
Im(eml(ix, 1)) = sin(x)     exactly, to machine precision
```

And the real part:

```
Re(eml(ix, 1)) = cos(x)     exactly
```

---

## Using complex_eval

```python
from monogate import sin_via_euler, cos_via_euler
import math

# Exact sin(x) via Euler path — one EML node
x = math.pi / 6
print(sin_via_euler(x))               # 0.5000000000000001
print(abs(sin_via_euler(x) - 0.5))    # < 1e-15

# Exact cos(x)
print(cos_via_euler(0.0))             # 1.0
print(cos_via_euler(math.pi))         # -1.0
```

---

## The Euler path node

```python
from monogate import euler_path_node, eval_complex, formula_complex

node = euler_path_node()
print(formula_complex(node))          # eml(ix, 1.0)

import math
z = eval_complex(node, math.pi / 4)
print(z.real)   # cos(pi/4) ≈ 0.7071...
print(z.imag)   # sin(pi/4) ≈ 0.7071...
```

---

## Complex EML operator

```python
from monogate import eml_complex
import cmath, math

# Basic complex EML
z = eml_complex(1j * math.pi, 1.0)   # exp(i*pi) - ln(1)
print(z.real)   # cos(pi) = -1.0
print(z.imag)   # sin(pi) ≈ 0 (machine precision)

# Complex ln uses the principal branch
z2 = eml_complex(1.0, 1j)            # exp(1) - ln(i)
```

---

## Complex terminal grammar

For MCTS / Beam search with complex terminals, use the extended grammar:

```python
from monogate import COMPLEX_TERMINALS
print(COMPLEX_TERMINALS)   # [1.0, 'x', 'ix', 'i']
```

Terminals:

| Terminal | Value |
|----------|-------|
| `1.0` | constant 1 |
| `"x"` | real input x |
| `"ix"` | imaginary input i·x |
| `"i"` | imaginary unit i = √−1 |

---

## Searching for complex approximations

```python
from monogate.complex_eval import score_complex_projection, COMPLEX_TERMINALS
from monogate import euler_path_node
import math

probe_x = [-2.0 + 4.0 * i / 49 for i in range(50)]
probe_y = [math.sin(xi) for xi in probe_x]

node = euler_path_node()
mse  = score_complex_projection(node, probe_x, probe_y, projection="imag")
print(f"MSE = {mse:.2e}")   # MSE = 0.00e+00 (exact)
```

---

## Pythagorean identity verification

The Euler path satisfies `sin²(x) + cos²(x) = 1` to machine precision:

```python
from monogate import sin_via_euler, cos_via_euler
import math

for x in [0.0, 0.5, 1.0, math.pi, -2.7]:
    s, c = sin_via_euler(x), cos_via_euler(x)
    assert abs(s*s + c*c - 1.0) < 1e-13
```
