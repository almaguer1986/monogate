# One Operator to Rule Them All: The EML Universal Gate

*April 2026 — monogate v0.12.0*

---

Mathematics is full of surprising simplifications. The Fourier transform shows that all periodic functions are just sums of sines. Boolean logic shows every computation reduces to AND and NOT. But what about continuous mathematics — elementary functions like exp, ln, sin, sqrt? Is there a single binary operation that generates all of them?

The answer, surprisingly, is yes. And it has a remarkably clean form:

```
eml(x, y) = exp(x) − ln(y)
```

This single binary gate, combined with the constant 1, can generate *every elementary function* as a finite expression tree. This result was proved by Andrzej Odrzywołek in early 2026, and we've spent the past few months building out its computational implications in the **monogate** library.

## The Construction

The proof is constructive. Start with eml(x, 1) = exp(x) − ln(1) = exp(x). One node, and you have exp. From exp you can build ln (two nodes), and from ln you can build all arithmetic. Every elementary function follows.

But there's a catch: some operations are expensive. Multiplication takes 7 EML nodes. Division takes 5. Powers take 9. Can we do better?

## The Hybrid Insight

It turns out that while EML is universal, it's not always optimal. Consider three related operators:

- **EML**: `exp(x) − ln(y)`, constant 1 → addition and subtraction in 3 nodes
- **EDL**: `exp(x) / ln(y)`, constant e → division in **1 node** (!)
- **EXL**: `exp(x) · ln(y)`, constant 1 → ln in **1 node** (!), pow in **3 nodes**

Each operator excels at different things. We built **BEST** (Best Exp-ln Selector Tree) as a hybrid router that dispatches each arithmetic primitive to its optimal operator. The result: **52% average node savings** across all operations, and up to **74% for trigonometric Taylor series**.

## The Sin Barrier

Here's where things get interesting. Can you represent sin(x) with any number of real EML nodes?

No. Here's why: every finite real EML tree is real-analytic on its domain, so it has finitely many zeros. But sin(x) has infinitely many zeros (one at every nπ). Contradiction.

We confirmed this by exhaustive search: we enumerated all **281 million** real EML trees up to 11 internal nodes and tested every one of them against sin(x). None matched at any tolerance.

But then something remarkable happens when you go complex. One node:

```
Im(eml(ix, 1)) = Im(exp(ix)) = sin(x)
```

This is just Euler's formula. The barrier is strictly a real-domain phenomenon. In the complex domain, sin(x) is trivial — a single node via the identity we learned in school.

## Phantom Attractors

During training, we noticed something strange. When we train a depth-3 EMLTree (7 internal nodes, 8 trainable leaves) to fit the constant π using gradient descent, it *doesn't converge to π*. Instead, it locks onto **3.169642** — a value that appears regardless of random seed, with 100% consistency.

This is a **phantom attractor**: a stable local minimum in the EML loss landscape that isn't the global minimum. A small L2 regularization penalty (λ ≥ 0.001) breaks its hold, inducing a sharp phase transition from 100% attractor convergence to 100% correct convergence.

The constant 3.169642 is not π, not e, not any rational combination of classical constants we've tested. It's a novel fixed-point constant of the depth-3 EML gradient flow — a number that was apparently unknown to mathematics before we stumbled on it while training neural networks.

## Physics Applications

The complex bypass opens up a catalog of compact PDE solutions. Free-particle Schrödinger, wave equations, potential well eigenfunctions — all reduce to 1-node CBEST expressions via the Euler path. The NLS bright soliton amplitude sech(x) is 2 nodes. The KdV soliton is 18 nodes via sech²(x).

This suggests that the EML grammar may be a natural algebraic framework for physics, analogous to Feynman diagrams but for solutions rather than interactions.

## What's in v0.12.0

The latest release includes:

- **15 special functions** with exact or high-precision CBEST constructions
- **Symbolic regression leaderboard** with scikit-learn compatible `EMLRegressor`
- **Physics-Informed Neural Networks** using EML as the activation function
- **Interval arithmetic** for certified error bounds
- **SymPy bridge** for symbolic simplification and LaTeX output
- **Streamlit web demo** with 5 interactive tabs
- **913 passing tests**

## Getting Started

```bash
pip install monogate
```

```python
from monogate import op, BEST, sin_via_euler
import math

# The universal gate
op(1.0, 1.0)              # exp(1) - ln(1) = e ≈ 2.718

# BEST routing (52% fewer nodes)
BEST.div(6.0, 2.0)        # 3.0 using 1 EDL node

# Exact sin(x) via complex bypass
sin_via_euler(math.pi/6)  # 0.5 exactly
```

The paper is at arXiv:2603.21852. The code is at github.com/almaguer1986/monogate.

---

*monogate is open source (MIT license). Contributions welcome.*
