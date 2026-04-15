# Operator Cousins of EML: Completeness, Efficiency, and Hybrid Architectures

## Abstract

The EML operator — eml(x,y) = exp(x) − ln(y) — was introduced by Odrzywołek (2026) as a universal primitive for elementary function computation from the single constant 1. We present theoretical and empirical extensions. Among the five natural binary operators of the form f(exp(x), ln(y)), we find that EML and EDL are the only candidates supporting complete elementary arithmetic; EML completeness is established by the original paper, and EDL completeness over the multiplicative group is demonstrated here. We identify EXL (exl(x,y) = exp(x)·ln(y)) as a numerically superior incomplete operator enabling 1-node ln and 3-node pow constructions, and establish that addition and subtraction are structurally irreplaceable in EML — no other complete operator in the family supports them. A HybridOperator framework routing each primitive to its optimal operator achieves 52% fewer nodes overall across all elementary operations, rising to 74% for polynomial evaluation patterns; applied to Taylor sin(x), machine precision (6.5e-15) is reached at 13 terms and 108 nodes. We also report five empirical phenomena from gradient-based symbolic regression and empirical results showing EXL-inner/EML-outer hybrid networks outperform pure-EML on 5/7 regression targets. The open problem of exact closed-form sin(x) from terminal {1} remains open. Code: github.com/almaguer1986/monogate.

---

## 1. Introduction

The question of whether a complex system can be generated from a single primitive has a long history in mathematics and computer science. In Boolean logic, the NAND gate suffices for all of discrete computation. Odrzywołek (2026) established an analogous result for continuous mathematics: the binary operator eml(x,y) = exp(x) − ln(y), paired with the constant 1, generates the full repertoire of elementary arithmetic. Every elementary function — addition, multiplication, exponentiation, logarithm, negation, division — can be expressed as a finite binary tree of identical EML nodes. The result was unexpected; it was found by systematic exhaustive search rather than mathematical intuition, and no comparable primitive had previously been known for continuous mathematics.

In this note we report empirical and theoretical extensions developed through systematic implementation of the EML framework. Working from the original paper, we implemented a complete EML arithmetic library, extended it to complex numbers, built a gradient-based symbolic regression engine, and explored the broader family of exp-ln binary operators. This investigation produced five named empirical phenomena in EML symbolic regression, identified structural properties of the operator family, and yielded a practical HybridOperator framework reducing node counts by 52–74% over pure EML. The open problem of exact closed-form constructions for sin(x) and cos(x) from terminal {1} remains open; we provide evidence bearing on its difficulty.

## 2. Methods

**EML Library Implementation.** We implemented the EML operator and derived arithmetic in JavaScript (npm: monogate) and Python (pip: monogate), with full test suites (109 and 299 tests respectively). The Python implementation includes differentiable EML trees via PyTorch autograd, supporting gradient-based optimization of leaf parameters. Complex number support was added following the principal-branch convention with ln(0) undefined, enabling constructions over ℂ.

**Gradient-Based Search Engine.** We developed a search framework combining fixed-topology EML expression trees with gradient-based leaf optimization. For a given tree topology with n internal nodes, leaf values are treated as trainable parameters and optimized with Adam (typically 2000–3000 steps, lr=1e-2). Multiple restarts per topology detect phantom attractors — cases where all restarts converge to the same suboptimal basin. For function approximation, each leaf is replaced by a learned affine function of the input (EMLNetwork), trained on uniform grids of 100–512 points.

**Experimental Setup.** All experiments ran on CPU in float32 (float64 for analytical verification). Targets included scalar constants (e, 0, π) and functions sampled on uniform grids (sin(x), cos(x), exp(x), x³, and polynomial targets). Node counts follow the convention of the original paper: internal EML operator nodes only, leaf terminals not counted.

## 3. Results

**Phantom Attractors.** Gradient descent on EMLTree targeting e converged to eml(eml(0.45, 1), eml(1, 1)) across all random restarts, regardless of complexity penalty λ. This construction evaluates to approximately e but is not the minimal known construction eml(1,1). Increasing λ from 0.01 to 2.0 degraded accuracy monotonically without escaping the attractor. Forcing minimality via a strong leaf-pull-to-1 penalty increased MSE by 10,518% relative to the unconstrained optimum. We term these locally stable non-minimal constructions phantom attractors (experiment_02).

**Lambert W Fixed Point.** Analysis of the right-chain topology eml(1, eml(1, eml(1, ...))) with all-ones leaves reveals convergence to W(eᵉ) ≈ 2.0168 — the fixed point of the iteration y → e − ln(y). This connects EML tree iteration to Lambert W function theory. The convergence is algebraically exact: W(eᵉ) satisfies W(eᵉ)·exp(W(eᵉ)) = eᵉ by definition of Lambert W, and e − ln(W(eᵉ)) = W(eᵉ) by substitution (experiment_05, Part A).

**Affine Leaf Necessity.** When EMLTree leaf parameters are constrained near 1 via strong L1 penalty (λ=20), the right-chain output converges to W(eᵉ) ≈ 2.0168 regardless of tree depth, with MSE > 4.0 for sin(x). Since sin(x) is periodic and W(eᵉ) is a constant, no pure {1}-terminal right-chain construction can represent sin(x). Relaxing to affine leaves (w·x + b) reduces MSE to 3.21e-4 at depth 4. We conclude affine leaves are necessary for periodic function approximation under right-chain topology (experiment_05, Part C).

**Left-Right Information Asymmetry.** An ablation study on depth-5 right-chain EMLNetwork for sin(x) fixed alternating halves of leaf parameters. Fixing the right half of leaves increased MSE by 100x relative to the all-free baseline (MSE 2.60e-1 vs 3.24e-3). Fixing the left half increased MSE by only 1.5x (MSE 4.91e-3). This asymmetry indicates the left subtree encodes function behavior while the right subtree encodes domain scaling — a structural property of EML trees not previously documented (experiment_05, Part D).

**Optimal Topology Bias.** A search across all Catalan topologies at depths 1–5 for sin(x) and cos(x) found that mildly left-heavy topologies (balance score 1) consistently outperform both right-chain (score 3+) and perfectly balanced (score 0) topologies. Perfect balance scored worst in its depth class for sin(x) (MSE 4.2e-3). The winning topology for cos(x) — eml(eml(·,eml(·,·)),eml(eml(·,·),·)) — is mirror-symmetric at depth 3 with balance score 1 (experiment_06).

**Best Known Compact Approximations.** The hybrid search yielded best-known compact numerical EML approximations for sin(x) and cos(x). For sin(x): topology eml(eml(1,eml(1,1)),eml(eml(1,1),1)), 4 nodes, MSE 3.21e-4 over [0, 2π] with affine leaves. For cos(x): topology eml(1,eml(eml(1,eml(1,1)),1)), 4 nodes, MSE 1.91e-4. These are numerical approximations with learned affine leaf parameters; the open problem of exact closed-form constructions from terminal {1} remains unsolved (experiments_04–06).

**HybridOperator and Node Reduction.** Analysis of the exp-ln operator family identified EDL (edl(x,y) = exp(x)/ln(y)) and EXL (exl(x,y) = exp(x)·ln(y)) as cousins with complementary strengths: EXL achieves 1-node ln and 3-node pow versus EML's 3-node and 15-node respectively; EDL achieves 1-node div versus EML's 15-node. A HybridOperator routing each primitive to its optimal operator achieves 52% fewer nodes overall and 74% fewer for polynomial evaluation patterns. Applied to Taylor sin(x), BEST reaches machine precision (6.5e-15) at 13 terms and 108 nodes versus 245 nodes for pure EML. Addition and subtraction are structurally irreplaceable in EML — no other complete operator in the family supports them (operator-cousins branch).

## 4. Discussion

The phantom attractor phenomenon suggests EML symbolic regression has a rugged loss landscape with many local minima that are mathematically valid but non-minimal. Standard gradient descent with complexity penalties is insufficient to escape them; discrete search or combinatorial methods may be required.

The 74% node reduction from HybridOperator is not a free lunch — it requires accepting three distinct operator types in one tree. The practical question for hardware implementation is whether a unified EML gate or a small family of specialized gates is preferable. The BEST routing table provides the answer for software; the hardware question remains open.

The additive irreplaceability of EML is a structural constraint on the operator family. Any future search for a "better" universal operator must either include addition natively or accept EML as the addition substrate.

The affine leaf necessity result closes one direction of the sin(x) open challenge: pure {1}-terminal right-chain topologies cannot produce periodic functions. Other topology classes remain unexplored under the strict grammar.

EXL's numerical superiority for deep trees (no catastrophic cancellation from subtraction) suggests it may be preferable as a neural network activation function, even though it is theoretically incomplete.

## 5. Open Problems

Does any finite EML tree with only terminal {1} evaluate to sin(x) exactly? The affine leaf necessity result rules out right-chain topologies; other topology classes remain open.

Is there an analytical proof that BEST achieves exactly 74% node reduction for polynomial evaluation? The empirical result is consistent but a proof would generalize to other function classes.

Can phantom attractors be escaped by discrete search methods (exhaustive enumeration, MCTS, genetic algorithms)? The exhaustive search tool at monogate.dev/search provides infrastructure for this investigation.

What is the theoretical explanation for the Lambert W fixed point connection? The algebraic derivation is clean but the deeper reason EML iteration converges to W(eᵉ) rather than another fixed point is not understood.

Is EDL complete over the full elementary function set, or only over the multiplicative group? A complete EDL derivation matching the original paper's function list would settle this.

## References

Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852v2 [cs.SC].

monogate — community implementation and extensions. github.com/almaguer1986/monogate

npm: npmjs.com/package/monogate

PyPI: pypi.org/project/monogate
