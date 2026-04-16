# monogate — Research Ideas & Extensions

Concrete directions for post-v0.11.0 work, ordered by estimated value.
Each includes a working prototype sketch.

---

## Idea 1 — SymPy Bridge: EML Trees as Symbolic Expressions

**Value:** Makes monogate results interoperable with the entire SymPy ecosystem
(simplification, differentiation, LaTeX rendering, CAS integration).

**Core insight:** Every EML tree is a composition of `exp` and `log`, both of which
SymPy handles natively. Translating an EML tree to a SymPy expression is O(n) in
tree size.

**Prototype:**

```python
# python/monogate/sympy_bridge.py

def to_sympy(tree, x_sym=None):
    """Convert an EML tree (tuple or string terminal) to a SymPy expression."""
    import sympy as sp
    if x_sym is None:
        x_sym = sp.Symbol('x')
    if tree == '1':   return sp.Integer(1)
    if tree == 'x':   return x_sym
    if tree == 'ix':  return sp.I * x_sym
    if tree == 'i':   return sp.I
    _, left, right = tree
    L = to_sympy(left,  x_sym)
    R = to_sympy(right, x_sym)
    # eml(a, b) = exp(a) - ln(b); guard: use log (sympy principal branch)
    return sp.exp(L) - sp.log(R)

def simplify_eml(tree):
    """Return sympy.simplify(to_sympy(tree))."""
    import sympy as sp
    expr = to_sympy(tree)
    return sp.simplify(expr)

def latex_eml(tree):
    """Return LaTeX string for an EML tree."""
    import sympy as sp
    return sp.latex(to_sympy(tree))
```

**Usage:**
```python
from monogate.sympy_bridge import to_sympy, latex_eml
from monogate import BEST

# Build an EML mul tree
# mul(a,b) in EDL = exp(ln(a) + ln(b))
tree = ('eml', ('eml', '1', 'x'), ('eml', '1', ('eml', '1', 'x')))
expr = to_sympy(tree)
print(expr)          # SymPy expression
print(latex_eml(tree))  # LaTeX
```

**What this unlocks:**
- Verify EML identities symbolically (SymPy `equals()`)
- Auto-simplify near-miss MCTS results
- Render EML trees in Jupyter as proper math
- Export to Wolfram Alpha / Mathematica

---

## Idea 2 — Symbolic Regression Leaderboard Mode

**Value:** Turns monogate into a self-contained symbolic regression benchmark tool,
comparable to PySR or gplearn, but with EML-specific operators.

**Core insight:** The existing MCTS + Beam search infrastructure just needs a
standardized benchmark runner and score table.

**Prototype:**

```python
# python/monogate/benchmark_sr.py

import math
import numpy as np
from dataclasses import dataclass
from typing import Callable

# Standard Nguyen benchmark functions (subset)
BENCHMARK_SUITE = {
    'nguyen-1':  (lambda x: x**3 + x**2 + x,              (-1, 1)),
    'nguyen-3':  (lambda x: x**5 + x**4 + x**3 + x**2 + x, (-1, 1)),
    'nguyen-5':  (lambda x: math.sin(x**2)*math.cos(x)-1, (0, math.pi)),
    'nguyen-7':  (lambda x: math.log(x+1)+math.log(x**2+1), (0, 2)),
    'keijzer-6': (lambda x: sum(1/i for i in range(1, int(x)+2)), (1, 50)),
}

@dataclass
class SRResult:
    problem: str
    best_formula: str
    best_mse: float
    n_nodes: int
    elapsed_s: float
    solved: bool   # MSE < 1e-4

def run_benchmark(n_simulations: int = 2000, depth: int = 5) -> list[SRResult]:
    from monogate.search import mcts_search
    results = []
    for name, (fn, (lo, hi)) in BENCHMARK_SUITE.items():
        probe = np.linspace(lo + 0.01, hi - 0.01, 40)
        import time
        t0 = time.perf_counter()
        r = mcts_search(fn, depth=depth, n_simulations=n_simulations,
                        probe_lo=lo, probe_hi=hi)
        elapsed = time.perf_counter() - t0
        results.append(SRResult(
            problem=name,
            best_formula=r.best_formula,
            best_mse=r.best_mse,
            n_nodes=r.best_formula.count('eml'),
            elapsed_s=elapsed,
            solved=r.best_mse < 1e-4,
        ))
    return results

def print_leaderboard(results: list[SRResult]) -> None:
    print(f'  {"Problem":<14} {"MSE":>10}  {"Nodes":>7}  {"Solved":>7}  {"Time":>7}  Formula')
    print('  ' + '-'*75)
    for r in sorted(results, key=lambda x: x.best_mse):
        solved = 'YES' if r.solved else 'no'
        print(f'  {r.problem:<14} {r.best_mse:>10.3e}  {r.n_nodes:>7}  {solved:>7}  '
              f'{r.elapsed_s:>6.1f}s  {r.best_formula[:35]}')
```

**What this enables:**
- Direct comparison with PySR / gplearn on standard benchmarks
- An arXiv-citable benchmark table for EML symbolic regression
- Community contributions (try your own search strategy, submit score)

---

## Idea 3 — Streamlit Web App

**Value:** Zero-install interactive demo that anyone can open from the arXiv paper
page or HN post without a Python environment.

**Core insight:** The `best_optimize()` function is fast enough for a synchronous
Streamlit app. MCTS search can run in a background thread.

**Prototype (`apps/streamlit_demo.py`):**

```python
import streamlit as st
import math
import monogate

st.set_page_config(page_title='monogate explorer', layout='wide')
st.title('monogate — EML Expression Optimizer')
st.caption('`eml(x,y) = exp(x) − ln(y)` — one operator, every elementary function')

# ── Sidebar ──────────────────────────────────────────────────────────────────
mode = st.sidebar.radio('Mode', ['Expression Optimizer', 'BEST Routing Table',
                                  'Complex BEST (sin in 1 node)', 'About'])

if mode == 'Expression Optimizer':
    st.subheader('Paste any Python / NumPy / PyTorch expression')
    expr = st.text_area('Expression', value='torch.sin(x)**2 + torch.cos(x) * x**3',
                        height=80)
    if st.button('Optimize', type='primary'):
        with st.spinner('Analyzing...'):
            try:
                r = monogate.best_optimize(expr)
                col1, col2, col3 = st.columns(3)
                col1.metric('Original nodes', r.total_eml)
                col2.metric('BEST nodes', r.total_best)
                col3.metric('Savings', f'{r.savings_pct:.0f}%')
                st.code(r.rewritten_code, language='python')
                st.dataframe(r.ops_table)
            except Exception as e:
                st.error(f'Parse error: {e}')
                st.info('Use torch.sin / np.exp notation')

elif mode == 'Complex BEST (sin in 1 node)':
    st.subheader('Im(eml(ix, 1)) = sin(x) — 1 complex node, exact')
    x_val = st.slider('x', 0.0, 2 * math.pi, 1.0, 0.01)
    from monogate import CBEST, im, re
    z = CBEST.sin(x_val)
    col1, col2, col3 = st.columns(3)
    col1.metric('im(CBEST.sin(x))',  f'{im(z):.8f}')
    col2.metric('math.sin(x)',       f'{math.sin(x_val):.8f}')
    col3.metric('Error',             f'{abs(im(z) - math.sin(x_val)):.2e}')
    st.caption('Real BEST Taylor series: 63 nodes for 8 terms. CBEST: 1 node.')

elif mode == 'About':
    st.markdown(open('README.md').read() if __import__('pathlib').Path('README.md').exists()
                else 'See github.com/almaguer1986/monogate')
```

**Deploy:**
```bash
pip install streamlit monogate
streamlit run apps/streamlit_demo.py
# Deploy to Streamlit Cloud: push to GitHub, connect repo, done.
```

---

## Idea 4 — New Special Functions via Complex MCTS

**Value:** The complex terminal set `{1, x, ix, i}` has barely been explored.
Several classical special functions likely have compact EML constructions.

**Concrete candidates to search:**

```python
import cmath, math

targets = {
    # Gamma function (real, x > 0) — Stirling approximation basis
    'ln_gamma': lambda x: math.lgamma(x),

    # Digamma (logarithmic derivative of Gamma)
    'digamma':  lambda x: (math.lgamma(x + 1e-5) - math.lgamma(x - 1e-5)) / 2e-5,

    # Fresnel S integral (via complex Euler: Im(exp(i·π·x²/2)))
    'fresnel_s': lambda x: cmath.phase(cmath.exp(1j * math.pi * x**2 / 2)) / math.pi,

    # Complex Gamma on imaginary axis (related to Riemann xi)
    'abs_gamma_half_plus_it': lambda t: abs(cmath.exp(
        sum(cmath.log(n + 0.5 + 1j*t) - cmath.log(n + 1j*t)
            for n in range(1, 20))
    )),
}
```

**Key search insight for Fresnel S:**
`Fresnel_S(x) = Im(exp(i·π·x²/2)) = Im(eml(i·π·x²/2, 1))`

This is exactly 1 complex EML node if `x²` is treated as a compound terminal —
or 2 nodes if `pow(x, 2)` is included. A paper result.

**Prototype search:**
```python
from monogate import complex_mcts_search
import cmath, math

# Search for a compact complex EML expression for Fresnel_S
result = complex_mcts_search(
    target_fn=lambda x: cmath.sin(math.pi * x**2 / 2).real,
    projection='real',
    depth=5,
    n_simulations=5000,
    probe_lo=0.1,
    probe_hi=2.0,
)
print(result.complex_formula, result.best_mse)
```

---

## Idea 5 — EML Interval Arithmetic

**Value:** If each leaf carries an interval `[lo, hi]` instead of a scalar, you can
compute guaranteed bounds on EML expression outputs — useful for formal verification,
sensitivity analysis, and safety-critical ML.

**Core insight:** `eml(a, b) = exp(a) - ln(b)`. Both `exp` and `ln` are monotone,
so interval arithmetic is exact (no wrapping):

```python
from dataclasses import dataclass

@dataclass
class Interval:
    lo: float
    hi: float
    def __repr__(self): return f'[{self.lo:.4g}, {self.hi:.4g}]'

def eml_interval(a: Interval, b: Interval) -> Interval:
    import math
    # exp is monotone increasing
    exp_lo = math.exp(a.lo)
    exp_hi = math.exp(a.hi)
    # ln is monotone increasing; b must be > 0
    assert b.lo > 0, f"b.lo = {b.lo} <= 0: ln undefined"
    ln_lo = math.log(b.lo)
    ln_hi = math.log(b.hi)
    # eml = exp(a) - ln(b)
    # min when exp(a) is min and ln(b) is max
    return Interval(exp_lo - ln_hi, exp_hi - ln_lo)

# Example: bound eml(x, 1) for x ∈ [0, 1]
x_interval = Interval(0.0, 1.0)
one_interval = Interval(1.0, 1.0)
result = eml_interval(x_interval, one_interval)
print(f'eml([0,1], 1) = {result}')   # [exp(0)-ln(1), exp(1)-ln(1)] = [1, e]
# True: eml(x,1) = exp(x) - ln(1) = exp(x), and exp([0,1]) = [1, e]
```

**What this unlocks:**
- Certified bounds on SIREN/NeRF outputs for input ranges
- Safety verification for EML-based control policies
- Inclusion in the `best_optimize()` output as a stability annotation

---

*These ideas are ordered by expected research impact. C1, C3, C5 from THEORY.md
remain the highest-priority open problems — any of the above ideas would be bonus
contributions, not replacements for cracking those conjectures.*
