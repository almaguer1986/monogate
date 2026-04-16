# monogate — Theoretical Foundations and Open Research Agenda

**Version:** v0.10.0 / Phase 11  
**Preprint:** arXiv:2603.21852 (Odrzywołek, 2026)  
**Source:** https://github.com/almaguer1986/monogate  

This document is the canonical theoretical reference for the monogate project.
It collects formal definitions, established theorems, open conjectures, and a
structured research roadmap for the community.  It is intended to be
self-contained for mathematically trained readers and is the primary reference
for anyone who wants to build on the EML operator framework.

---

## 1. The EML Universal Operator

**Definition 1.1 (EML operator).**  
Let $\mathbb{F}$ denote $\mathbb{R}$ or $\mathbb{C}$.  The *EML operator* is
the binary function
$$
  \operatorname{eml} : \mathbb{F} \times \mathbb{F}_{>0} \to \mathbb{F},
  \qquad
  \operatorname{eml}(a, b) \;=\; e^a - \ln b.
$$
Over $\mathbb{C}$ the logarithm is taken on its principal branch
($\operatorname{Im}(\ln b) \in (-\pi, \pi]$).

**Definition 1.2 (EML expression tree).**  
An *EML tree of depth $d$ with terminal set $\mathcal{T}$* is a complete
binary tree of depth $d$ in which every leaf is labeled by an element of
$\mathcal{T}$ and every internal node computes $\operatorname{eml}$ of its
two children.  The tree evaluates recursively; the right child of each internal
node is passed through $\operatorname{softplus}$ during numerical evaluation to
keep it in the domain of $\ln$.

**Theorem 1.3 (EML completeness, Odrzywołek 2026).**  
Every elementary function can be expressed as a finite EML tree over the
terminal set $\{1\}$.  In particular, $e^x$, $\ln x$, $x^r$ ($r \in \mathbb{Q}$),
$\sin x$, $\cos x$, $\operatorname{erf} x$, and all rational compositions
thereof admit exact EML tree representations.

The number of internal nodes required is the *EML node count* of a function —
a complexity measure analogous to circuit depth in Boolean complexity theory.

**Definition 1.4 (BEST routing, monogate v0.9.0).**  
The *BEST hybrid operator* is a dispatcher that selects among three EML
operator families — EML ($e^a - \ln b$), EDL ($e^a / \ln b$), and
EXL ($e^a \cdot \ln b$) — per operation to minimise node count.  The routing
rules are: EXL for $\ln$ and $\operatorname{pow}$ (1 and 3 nodes respectively),
EDL for $\operatorname{mul}$, $\operatorname{div}$, $\operatorname{recip}$
(7, 1, 2 nodes), EML for $\operatorname{add}$, $\operatorname{sub}$,
$\operatorname{exp}$ (11, 5, 1 nodes).  Combined, BEST reduces node count by
52% on average across the standard nine operations, and by 74% for
Taylor-series approximations of $\sin / \cos$.

---

## 2. The Infinite Zeros Barrier

**Theorem 2.1 (Infinite Zeros Barrier).**  
*No finite EML tree with terminal set $\{1, x\}$ and real-valued evaluation
can satisfy $T(x) = \sin(x)$ for all $x \in \mathbb{R}$.*

*Proof.*  
Every finite composition of $\exp$ and $\ln$ over $\mathbb{R}$ is
real-analytic on any open interval where the argument to $\ln$ remains
positive.  By the identity theorem for real-analytic functions, a non-zero
real-analytic function has at most countably many zeros that are isolated (i.e.,
it cannot have a limit point of zeros in its domain).  In particular, on any
bounded interval $[-R, R]$ the number of zeros is finite.  The function
$\sin(x)$ has a zero at every $k\pi$ for $k \in \mathbb{Z}$, so it has
infinitely many zeros in $[-R, R]$ for large $R$.  No real-analytic function
with finitely many zeros on bounded intervals can equal $\sin(x)$.  $\square$

**Corollary 2.2.**  
The same argument applies to any target function with infinitely many real zeros,
including $\cos(x)$, Bessel $J_0(x)$, Airy $\operatorname{Ai}(x)$, and
$x^{1/n}\sin(1/x)$.

**Empirical support (v0.9.0).**  
Exhaustive enumeration of all $281{,}026{,}468$ EML trees with
$N \leq 11$ internal nodes and terminals $\{1, x\}$ found zero candidates
matching $\sin(x)$ at any tolerance from $10^{-4}$ to $10^{-9}$ (Table 3
of the preprint; `python/results/sin_n11.json`).

**Conjecture 2.3 (Complex EML sin barrier).**  
No finite EML tree with terminal set $\{1, x, ix, i\}$ and
*purely real-projection* evaluation satisfies $T(x) = \sin(x)$ for all
$x \in \mathbb{R}$ using only real arithmetic at each node.

*Remark.*  The known 1-node complex construction
$\operatorname{Im}(\operatorname{eml}(ix, 1)) = \sin(x)$
relies on the imaginary projection as an *extraction step*.  Conjecture 2.3
asks whether this projection step can be *folded* into a purely algebraic
EML identity without complex arithmetic at any intermediate node.  Current
evidence suggests it cannot — but no proof is known.

**Open Problem 2.4.**  
Determine the minimum-depth EML tree over $\{1, x\}$ achieving
$\mathrm{MSE} \leq 10^{-6}$ for $\sin(x)$ on $[-\pi, \pi]$.  The current
best known approximation achieves $\mathrm{MSE} = 1.478 \times 10^{-4}$ at
$N = 11$ (12 leaves, from the exhaustive search).

---

## 3. Complex-Domain Extensions and CBEST

**Definition 3.1 (Complex BEST operator).**  
The *CBEST operator* (v0.10.0, `monogate.complex_best`) applies the BEST
routing rules with $\mathbb{C}$-arithmetic throughout.  Routing is identical
to real BEST except that $\sin(x)$ and $\cos(x)$ are dispatched to the
*Euler path*:
$$
  \operatorname{CBEST.sin}(x)
  \;=\; \operatorname{eml}(ix, 1)
  \;=\; e^{ix}
  \;=\; \cos x + i\sin x,
\quad
  \operatorname{Im}(\cdot) \text{ extracts } \sin x.
$$

This reduces the node count for $\sin$ and $\cos$ from 63 (eight-term EXL
Taylor) to **1 each**.

**Theorem 3.2 (Euler path identity).**  
For all $x \in \mathbb{R}$:
$$
  \operatorname{Im}(\operatorname{eml}(ix, 1))
  = \sin(x), \qquad
  \operatorname{Re}(\operatorname{eml}(ix, 1))
  = \cos(x).
$$
*Proof.*  Direct application of Euler's formula: $e^{ix} = \cos x + i\sin x$
and $\ln 1 = 0$.  $\square$

**Open Problem 3.3 (CBEST completeness).**  
Is every real-analytic special function (Bessel, Airy, $\operatorname{erf}$,
hypergeometric) approximable to arbitrary precision by a finite EML tree over
$\{1, x, ix, i\}$ with imaginary projection?  The monogate complex MCTS
search finds near-exact constructions for $J_0$, $\operatorname{erf}$, and
$\operatorname{Ai}$ at modest node counts, but no formal completeness result
is known.

**Open Problem 3.4 (Minimum node counts for special functions).**  
Let $\mathcal{N}_\varepsilon(f)$ denote the minimum number of complex EML
nodes needed to approximate $f$ to within $\varepsilon$ in $L^\infty$ on a
bounded interval.  Determine tight bounds on $\mathcal{N}_\varepsilon(J_0)$,
$\mathcal{N}_\varepsilon(\operatorname{Ai})$, and
$\mathcal{N}_\varepsilon(\operatorname{erf})$.  Current empirical estimates
from MCTS search: $\mathcal{N}_{10^{-4}}(J_0) \leq 7$,
$\mathcal{N}_{5\times10^{-4}}(\operatorname{erf}) \leq 5$,
$\mathcal{N}_{2\times10^{-3}}(\operatorname{Ai}) \leq 9$.

---

## 4. Phantom Attractors and the Optimization Landscape

**Definition 4.1 (Phantom attractor).**  
A *phantom attractor* of depth-$d$ EML tree gradient descent is a value
$\alpha^* \in \mathbb{R}$ such that: (i) $\alpha^*$ is not the intended
optimum, (ii) the gradient of the MSE loss vanishes at the leaf-parameter
configuration corresponding to $\alpha^*$, and (iii) the basin of attraction
of $\alpha^*$ covers a positive-measure set of initial conditions.

**Empirical result (v0.9.0).**  
For depth-3 EMLTree trained toward $\pi$ with $\ell_1$ penalty weight
$\lambda = 0$: the phantom attractor value is $\alpha^* \approx 3.1696$.
All 40 random seeds converge to $\alpha^*$.  At the critical penalty
$\lambda_{\mathrm{crit}} = 0.001$, all 40 seeds converge to $\pi$.

**Open Problem 4.2 (Attractor identification).**  
What is the exact value of $\alpha^* \approx 3.1696$?  Is it:
(a) a transcendental fixed point of the depth-3 EML gradient flow,
(b) a root of a polynomial with EML coefficients, or
(c) a rational combination of $e$, $\pi$, $\ln 2$, or other constants?

**Conjecture 4.3 (Sharp phase transition).**  
For every target $t \in \mathbb{R}$ and depth $d \geq 2$, there exists a
critical regularisation strength $\lambda_{\mathrm{crit}}(t, d) > 0$ such
that for all $\lambda > \lambda_{\mathrm{crit}}$ gradient descent on a
depth-$d$ EMLTree converges to $t$ from every starting point in a set of
full measure.

**Open Problem 4.4 (Characterise all phantom attractors).**  
A complete enumeration of phantom attractors for depth-3 EML trees has not
been carried out.  The 2D attractor landscape (`experiments/plot_attractor_landscape.py`)
reveals one dominant false basin at $\approx 3.1696$; it is unknown whether
other attractors exist at different target values or tree depths.

---

## 5. Physics-Informed EML Networks

**Definition 5.1 (EMLPINN).**  
A *Physics-Informed EML Network* (`monogate.pinn.EMLPINN`, v0.10.0) is an
`nn.Module` consisting of: (i) an `EMLNetwork` backbone of depth $d$ with
$2^d$ linear leaves, and (ii) a physics residual computed via automatic
differentiation.  Training minimises
$$
  \mathcal{L} = \mathrm{MSE}(\hat{u}(x_{\mathrm{data}}),\, y_{\mathrm{data}})
              + \lambda_{\mathrm{phys}} \cdot
                \frac{1}{M}\sum_{j=1}^{M} \mathcal{R}(\hat{u};\, x_j)^2
$$
where $\mathcal{R}$ is the ODE/PDE residual, computed by
`torch.autograd.grad` with `create_graph=True`.

**Interpretability property.**  
Because the backbone is an EML tree with linear leaves, the learned model
admits a human-readable symbolic formula at any training step via
`model.formula(["x"])`.  This makes EMLPINN a *symbolic-numeric hybrid*: it
trains like a neural network but produces an expression that can be inspected,
manipulated, and compared against known analytical solutions.

**Open Problem 5.2 (Symbolic identification via PINN).**  
Given a solution $\hat{u}$ returned by a converged EMLPINN, can the symbolic
formula produced by `model.formula(["x"])` be simplified to a known closed
form (e.g.\ $A\sin(\omega x + \phi)$ for the harmonic oscillator)?  
Developing automated simplification procedures for EML formulas is an open
engineering and mathematical problem.

---

## 6. Open Conjectures and Problems (Numbered Index)

The following is a collected index of formal open problems, ordered by
estimated tractability.

**C1.** *(EDL additive incompleteness)*  
No finite EDL tree — $\operatorname{edl}(a,b) = e^a / \ln b$ — with terminal
set $\{e\}$ evaluates to $a + b$ or $a - b$ for all $a, b \in \mathbb{R}$.
Exhaustive search over all 196 EDL trees with $N \leq 6$ internal nodes
(`python/experiments/edl_completeness/`) found zero additive constructions.
A formal proof remains open.

**C2.** *(Complex EML $\sin$ without projection)*  
There is no finite EML tree over $\{1, x, ix, i\}$ that evaluates to $\sin(x)$
for all $x \in \mathbb{R}$ using only real arithmetic at every intermediate
node (i.e., without an imaginary-projection extraction step).

**C3.** *(Phantom attractor value)*  
The phantom attractor $\alpha^* \approx 3.1696$ is a definite algebraic or
transcendental constant.  Its closed form is unknown.

**C4.** *(Sharp $\lambda_{\mathrm{crit}}$ formula)*  
For depth-3 EMLTree trained toward $\pi$:
$\lambda_{\mathrm{crit}} \in (0.001, 0.005)$.  A closed-form expression
for $\lambda_{\mathrm{crit}}$ as a function of tree depth, target value, and
initialisation distribution has not been derived.

**C5.** *(Optimal $N=12$ sin approximation)*  
The best real-EML approximation to $\sin(x)$ at $N = 12$ improves on the
$N = 11$ result ($\mathrm{MSE} = 1.478 \times 10^{-4}$).  The exact minimax
optimal value at $N = 12$ is unknown; GPU-accelerated MCTS search
(`gpu_mcts_search`) is the recommended approach.

**C6.** *(CBEST special function completeness)*  
Every real-analytic function is approximable to arbitrary precision by a
finite complex-EML tree over $\{1, x, ix, i\}$.

**C7.** *(EMLNetwork symbolic convergence)*  
An EMLPINN trained to convergence on the harmonic oscillator produces a
formula that is algebraically equivalent to $A\sin(\omega x + \phi)$ for
some learned $A, \phi$.  This would establish a symbolic convergence property
for EML-based PINNs.

---

## 7. Research Roadmap for the Community

The following items are ordered by suggested priority for community
contributions:

**T1. Crack the attractor value (Open Problem C3).**  
Numerically determine $\alpha^*$ to 50 decimal places and run integer-relation
algorithms (PSLQ, LLL) against bases $\{\pi, e, \ln 2, \gamma, \ldots\}$.
Tools: `mpmath`, `sympy.ntheory.lattice`.
If $\alpha^*$ has a closed form, it would be publishable.

**T2. Prove EDL additive incompleteness (Conjecture C1).**  
This is the cleanest open formal problem.  A structural argument based on
the multiplicative nature of EDL trees would be most direct.
Reference: `python/docs/research/findings.md`, §7 EDL Completeness in the
preprint.

**T3. N=12 exhaustive search.**  
Extend `python/monogate/search/sin_search_05.py` to $N = 12$.  Requires
approximately $4\times$ the compute of the $N = 11$ run (~20 CPU-minutes with
the vectorised evaluator) or ~2 minutes with GPU batch evaluation.
The `gpu_mcts_search` infrastructure is already in place.

**T4. Minimax-optimal EML approximation.**  
Use `beam_search(..., objective='minimax')` to find the Chebyshev-optimal
real-EML approximation to $\sin(x)$ at $N \leq 11$.  Compare the minimax
error against the known MSE-optimal result.

**T5. Automated EML formula simplification.**  
After EMLPINN convergence, apply computer-algebra simplification (SymPy, Mathematica)
to the formula string.  Develop a standardised pipeline from
`model.formula(["x"])` to a canonical symbolic form.

**T6. Complex MCTS for Bessel and Airy.**  
The current J₀ and Airy Ai constructions are empirical approximations from
MCTS with small simulation budgets.  Run larger MCTS searches (n_simulations ≥
50,000) and compute exact MSE bounds.  Attempt to identify the found trees
with known integral representations (Poisson, Airy integral).

**T7. EML in quantum computing.**  
The EML operator identity $\operatorname{eml}(ix, 1) = e^{ix}$ is the basic
rotation gate in quantum computing up to global phase.  Investigate whether
EML trees can represent quantum circuit amplitudes and whether BEST routing
has a quantum-circuit-complexity interpretation.

---

*This document is versioned with the monogate source code.*  
*For the authoritative preprint, see* `python/paper/preprint.tex` *and*
`python/PAPER.md`*.*  
*For reproduction instructions, see the* `Makefile` *at the repository root.*
