# monogate v0.9.0 — Launch Announcements

Ready-to-post text for each platform. Replace `ARXIV_ID_PLACEHOLDER` with the real arXiv ID
after running `python scripts/update_arxiv_id.py <ID>`.

---

## Hacker News

**Title:**
```
Show HN: monogate – one operator (eml = exp−ln) generates every elementary function; 281M-tree sin barrier search
```

**Body:**
```
I've been building monogate, a Python/Rust library that implements the EML operator
(eml(x,y) = exp(x) − ln(y)) from Odrzywołek 2026. From this single gate + the constant 1,
every elementary function is a finite binary expression tree.

The main result I want to share: sin(x) cannot be represented exactly by any finite
real-valued EML tree. I proved it (Infinite Zeros Barrier theorem) and confirmed it
empirically by exhaustively searching 281,026,468 trees (N ≤ 11, ~5 min on a laptop CPU
with a vectorised NumPy evaluator). Zero candidates at tolerances 1e-4 through 1e-9.

The workaround is one complex-domain node: Im(eml(i·x, 1)) = Im(exp(ix)) = sin(x) exactly.
Euler's formula resolves the barrier in one step.

Other things in the library:

- BEST routing: hybrid EML/EDL/EXL operator selection that cuts node count 52–74% and
  gives 2.8× wall-clock speedup on sin Taylor series
- EMLLayer: drop-in PyTorch activation for SIREN/NeRF/PINN, ONNX-exportable, torch.compile
  support
- Rust extension (monogate-core): 5.9× speedup over plain Python via PyO3/rayon
- Interactive explorer at monogate.dev with Attractor Lab, Optimizer tab, Research tab

Paper: https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER
GitHub: https://github.com/almaguer1986/monogate
PyPI: pip install monogate

Happy to answer questions about the search algorithm, the Barrier proof, or the BEST
routing decision logic.
```

---

## r/MachineLearning

**Title:**
```
[Project] monogate – EML universal operator for neural networks: one gate generates exp, ln, sin, GELU, etc. + 281M exhaustive sin search + Rust 5.9× speedup
```

**Body:**
```
**tl;dr:** A single binary operator eml(x,y) = exp(x) − ln(y), combined with BEST hybrid
routing (52–74% node reduction), gives a fully differentiable, ONNX-compatible PyTorch
activation layer that can replace sin in SIRENs and other periodic networks. New: 281M-tree
exhaustive search proves sin(x) has no finite real-valued EML representation.

---

**The operator:**
```python
eml(x, y) = exp(x) − ln(y)
```
From this gate + constant 1: exp, ln, sin (complex), GELU, sigmoid, tanh, softplus — all
exact expression trees. Based on Odrzywołek (arXiv:2603.21852).

**BEST routing:**
Selects EML/EDL/EXL per subtree. 52–74% fewer nodes, 2.8× faster sin Taylor series,
with no accuracy loss.

**PyTorch integration:**
```python
from monogate.torch import EMLLayer

layer = EMLLayer(256, 256, depth=2, operator="BEST", compiled=True)
# Rust backend auto-selected: 5.9× vs baseline Python tree
```
Drop-in for sin activation in SIREN. Full state_dict() / ONNX export (opset 17).

**The sin barrier:**
Theorem: No finite real EML tree equals sin(x). Proof: sin has infinitely many zeros;
finite EML trees are real-analytic with finitely many zeros. Contradiction.
Confirmed: 281,026,468 trees searched, 0 candidates.

**Performance:**
| Backend | Speedup |
|---------|---------|
| Standard | 1× |
| FusedEMLActivation | 3.6× |
| + torch.compile | 4.4× |
| Rust (monogate-core) | **5.9×** |

Paper: https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER
Code: https://github.com/almaguer1986/monogate
Interactive: https://monogate.dev
```

---

## r/math

**Title:**
```
New result: no finite real-valued EML tree (exp−log operator) can represent sin(x) — theorem + 281M exhaustive confirmation
```

**Body:**
```
A recent paper (Odrzywołek, 2026) showed that the binary operator
  eml(x, y) = exp(x) − ln(y),  with the constant 1,
generates every elementary function as a finite binary expression tree. For example:
  sin(x) requires an infinite series in EML — but only a *finite* complex construction.

I've been working on extensions to this operator and found a barrier result:

**Theorem (Infinite Zeros Barrier):**
No finite real-valued EML tree T with terminals {1, x} satisfies T(x) = sin(x) for all x ∈ R.

**Proof sketch:**
Every finite EML tree is real-analytic (composition of exp and log, extended by softplus for
numerical continuity). A non-zero real-analytic function on R has only finitely many zeros.
sin(x) has zeros at {kπ : k ∈ Z} — countably infinite. Contradiction. □

The corollary extends to cos(x), Bessel J₀(x), Airy Ai(x), and any function with infinitely
many real zeros.

**Complex bypass (exact, 1 node):**
Im(eml(i·x, 1)) = Im(exp(ix) − ln(1)) = Im(e^{ix}) = sin(x)
This is exact for all x ∈ R. The barrier is real-domain only.

**Empirical confirmation:**
I ran an exhaustive search over all EML trees with N ≤ 11 internal nodes
(281,026,468 trees total after parity filtering). Zero candidates at tolerances
1e-4, 1e-6, and 1e-9. Runtime: ~5 minutes on a single CPU core.

Paper: https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER
Code: https://github.com/almaguer1986/monogate

Open question: is there a cleaner proof that doesn't rely on the zero-counting argument?
(The real-analyticity argument is tight but requires extending the tree evaluation to softplus
for formal continuity — the raw EML tree has log domain restrictions.)
```

---

## X / Twitter (thread)

**Tweet 1 (hook):**
```
New result: searched 281 million expression trees.

None of them equal sin(x).

Not because we didn't find one—because we proved it's impossible.

[thread on the EML sin barrier]
```

**Tweet 2 (the operator):**
```
Start here: eml(x,y) = exp(x) − ln(y)

One operator + the constant 1 = every elementary function.
exp, ln, sqrt, GELU, sigmoid, tanh — all exact finite trees.

sin(x)? No tree exists. Theorem says so.
```

**Tweet 3 (the theorem):**
```
Theorem (Infinite Zeros Barrier):
No finite real EML tree equals sin(x).

Proof: sin has zeros at {kπ: k ∈ Z} — infinitely many.
Every EML tree is real-analytic → finitely many zeros.
Contradiction. □

Confirmed: 281,026,468 trees, 0 candidates.
```

**Tweet 4 (the bypass):**
```
But there's a 1-node exact answer in the complex domain:

Im(eml(i·x, 1)) = Im(exp(ix)) = sin(x)

Euler's formula resolves the barrier in one step.
The real domain is the restriction, not the operator.
```

**Tweet 5 (BEST routing):**
```
The library also has BEST routing — hybrid EML/EDL/EXL operator selection.

Result: 52–74% fewer nodes on sin Taylor series
        2.8× wall-clock speedup

eml vs edl vs exl per subtree, auto-selected.
```

**Tweet 6 (PyTorch):**
```
EMLLayer: drop-in PyTorch activation

layer = EMLLayer(256, 256, depth=2, compiled=True)
# Rust backend: 5.9× faster than baseline
# Works in SIREN, NeRF, PINN
# ONNX export, torch.compile, state_dict()

pip install monogate
```

**Tweet 7 (links):**
```
Paper: arxiv.org/abs/ARXIV_ID_PLACEHOLDER
Code: github.com/almaguer1986/monogate
Interactive explorer: monogate.dev

Try the sin barrier search yourself:
python monogate/search/analyze_n11.py
```

---

## LinkedIn (longer, professional tone)

**Post:**
```
Excited to share the result of several months of work on symbolic computation and neural
network operators.

monogate v0.9.0 is now live on arXiv and PyPI.

**The core idea:** A single binary operator, eml(x,y) = exp(x) − ln(y), together with the
constant 1, generates every elementary function as a finite expression tree. This was proved
by Odrzywołek (2026). I've been building practical extensions.

**The headline result:** No finite real-valued EML tree can represent sin(x). This is the
Infinite Zeros Barrier theorem — sin has infinitely many zeros, every EML tree has finitely
many, so they can never be equal. We confirmed this by exhaustively evaluating 281,026,468
trees (N ≤ 11), runtime 5 minutes on a laptop.

The complex-domain bypass: Im(eml(i·x, 1)) = sin(x) exactly (Euler's formula, 1 node).

**Practical results:**
- BEST routing: 52–74% node reduction, 2.8× speedup on periodic functions
- EMLLayer: drop-in PyTorch activation for SIREN/NeRF/PINN, fully differentiable,
  ONNX-compatible (opset 17)
- Rust extension: 5.9× throughput vs baseline Python

**arXiv:** https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER
**GitHub:** https://github.com/almaguer1986/monogate
**PyPI:** pip install monogate
```

---

*Update `ARXIV_ID_PLACEHOLDER` by running: `python scripts/update_arxiv_id.py <your-arxiv-id>`*
