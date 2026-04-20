#!/usr/bin/env python3
# encoding: utf-8
"""
NN-7: Activation Function Shootout — Mathematical Analysis.

Compares six activation functions across four task families
using SuperBEST v4 cost theory and gradient properties.

SuperBEST v4 costs:
  exp=1n, ln=1n, recip=1n, neg=2n, mul=2n, sub=2n, div=2n,
  sqrt=2n, pow=3n, add_pos=3n, add_gen=11n

Key insight:
  softplus(x) = ln(1 + exp(x))  ← this is LEAd(0, x) reversed, i.e., a 1n EML primitive.
  ReLU(x) = max(0, x)            ← not EML-representable; piecewise linear.
  sigmoid(x) = 1/(1+exp(-x))    ← DEML route + recip + add_pos ≈ 7n.
"""

from __future__ import annotations
from dataclasses import dataclass


# ── SuperBEST costs ───────────────────────────────────────────────────────────
COSTS: dict[str, int] = {
    "exp": 1, "ln": 1, "recip": 1, "neg": 2, "mul": 2,
    "sub": 2, "div": 2, "sqrt": 2, "pow": 3, "add_pos": 3, "add_gen": 11,
}


@dataclass(frozen=True)
class ActivationProfile:
    name: str
    formula: str
    superbest_cost: int | str   # int if EML-representable, "∞" or "N/A" otherwise
    eml_route: str              # how SuperBEST routes it
    gradient_formula: str
    vanishing_gradient: bool    # True = suffers vanishing gradient at saturation
    dying_neuron: bool          # True = can produce permanently 0-gradient neurons
    smooth: bool                # True = C-infinity smooth
    monotone: bool
    pinn_suitable: bool         # Physics-Informed NN suitability
    classification_suitable: bool
    sr_distillable: bool        # Can an EML tree distil this activation?
    notes: str


ACTIVATIONS: list[ActivationProfile] = [
    ActivationProfile(
        name="ReLU",
        formula="max(0, x)",
        superbest_cost="N/A",
        eml_route="Not representable — piecewise linear, not in EML family",
        gradient_formula="1 if x>0 else 0",
        vanishing_gradient=False,
        dying_neuron=True,
        smooth=False,
        monotone=True,
        pinn_suitable=False,
        classification_suitable=True,
        sr_distillable=False,
        notes=(
            "Gold standard for classification CNNs. Survives dead neurons via SGD "
            "momentum and batch norm. Not EML-distillable: the kink at x=0 requires "
            "infinite EML nodes (step function not in exp-ln closure). "
            "PINNs: fails because physics PDEs require smooth activation for "
            "automatic differentiation to match the PDE residual."
        ),
    ),
    ActivationProfile(
        name="sigmoid",
        formula="1 / (1 + exp(-x))",
        superbest_cost=7,
        eml_route="DEML(x,1)=exp(-x)=1n, add_pos(1,exp(-x))=3n, recip=1n → WRONG sign. "
                  "Correct: exp(-x)=1n, add_pos(1,exp_neg)=3n, recip=1n → total 5n. "
                  "But recip of sum needs care: full path = neg(x)+exp+add_pos+recip = 2+1+3+1 = 7n",
        gradient_formula="sigmoid(x) * (1 - sigmoid(x))",
        vanishing_gradient=True,
        dying_neuron=False,
        smooth=True,
        monotone=True,
        pinn_suitable=False,
        classification_suitable=True,
        sr_distillable=True,
        notes=(
            "Historical standard. Suffers vanishing gradient in deep nets: "
            "max gradient is 0.25 at x=0, decays exponentially for |x|>2. "
            "EML cost: neg(x)=2n + exp=1n + add_pos(1, exp_neg_x)=3n + recip=1n = 7n. "
            "Can be distilled to EML tree. Unsuitable for PINNs at depth because "
            "gradient saturation prevents PDE residual minimisation."
        ),
    ),
    ActivationProfile(
        name="tanh",
        formula="(exp(x) - exp(-x)) / (exp(x) + exp(-x))",
        superbest_cost=9,
        eml_route="EML(x,neg_x)+DEML+div: exp(x)=1n, exp(-x)=1n, "
                  "sub=2n, add_pos=3n, div=2n → 9n",
        gradient_formula="1 - tanh(x)^2",
        vanishing_gradient=True,
        dying_neuron=False,
        smooth=True,
        monotone=True,
        pinn_suitable=False,
        classification_suitable=True,
        sr_distillable=True,
        notes=(
            "Better than sigmoid (zero-centred output [-1,1] vs [0,1]) but still "
            "vanishes at saturation. EML cost = 9n. "
            "PINNs: gradient saturation for |x|>1.5 causes same issue as sigmoid. "
            "Distillable to EML tree at ~9 nodes."
        ),
    ),
    ActivationProfile(
        name="softplus",
        formula="ln(1 + exp(x))",
        superbest_cost=1,
        eml_route="LEAd(x, 1) = ln(exp(x) + 1) — direct 1-operator EML primitive (1n)",
        gradient_formula="sigmoid(x) = 1/(1+exp(-x))",
        vanishing_gradient=False,
        dying_neuron=False,
        smooth=True,
        monotone=True,
        pinn_suitable=True,
        classification_suitable=False,
        sr_distillable=True,
        notes=(
            "HEADLINE RESULT: softplus is a 1n EML operator (LEAd). "
            "Gradient = sigmoid(x), which is always in (0,1) — no dead neurons, "
            "no gradient cliff. Smooth everywhere (C-infinity). "
            "PINN insight: physics equations involve exp and ln naturally "
            "(Boltzmann, entropy, Arrhenius, Navier-Stokes). When the activation "
            "IS a 1n EML primitive, the EML symbolic head can distil the network "
            "into an exact closed-form expression. "
            "Classification: softplus is slower than ReLU, smoother but less sparse — "
            "not typically best for image classification benchmarks."
        ),
    ),
    ActivationProfile(
        name="GELU",
        formula="x * Phi(x)  [Phi = normal CDF]",
        superbest_cost="N/A",
        eml_route="Phi(x) = 0.5*(1+erf(x/sqrt(2))). erf not in EML closure. "
                  "Approx: 0.5*x*(1+tanh(sqrt(2/pi)*(x+0.044715*x^3))) — 30n+",
        gradient_formula="Phi(x) + x*phi(x)  [phi = normal PDF]",
        vanishing_gradient=False,
        dying_neuron=False,
        smooth=True,
        monotone=False,
        pinn_suitable=False,
        classification_suitable=True,
        sr_distillable=False,
        notes=(
            "State-of-the-art for transformers (BERT, GPT). "
            "erf is not in the EML operator closure — no finite EML representation. "
            "Tanh approximation is distillable at ~30n but loses precision. "
            "Good for self-attention because it stochastically gates inputs. "
            "Not suitable for EML distillation workflows."
        ),
    ),
    ActivationProfile(
        name="Swish",
        formula="x * sigmoid(x)",
        superbest_cost=9,
        eml_route="sigmoid=7n (see above), mul(x, sigmoid)=2n → 9n total",
        gradient_formula="sigmoid(x) + x*sigmoid(x)*(1-sigmoid(x))",
        vanishing_gradient=False,
        dying_neuron=False,
        smooth=True,
        monotone=False,
        pinn_suitable=False,
        classification_suitable=True,
        sr_distillable=True,
        notes=(
            "Non-monotone (has a local minimum near x≈-1.28). "
            "Outperforms ReLU on some deep net benchmarks. "
            "EML cost = 9n (sigmoid=7n + mul=2n). "
            "Distillable but costly. "
            "Not ideal for PINNs: non-monotonicity can create spurious "
            "solution branches in PDE residuals."
        ),
    ),
]


# ── Task-family suitability grid ──────────────────────────────────────────────
# Rating: 5=best, 1=worst
TASK_FAMILIES = ["Classification", "PINN", "SR distillation", "EML cost"]

SUITABILITY: dict[str, dict[str, int]] = {
    "ReLU":     {"Classification": 5, "PINN": 1, "SR distillation": 1, "EML cost": 1},
    "sigmoid":  {"Classification": 3, "PINN": 2, "SR distillation": 4, "EML cost": 3},
    "tanh":     {"Classification": 3, "PINN": 2, "SR distillation": 4, "EML cost": 3},
    "softplus": {"Classification": 2, "PINN": 5, "SR distillation": 5, "EML cost": 5},
    "GELU":     {"Classification": 5, "PINN": 3, "SR distillation": 1, "EML cost": 1},
    "Swish":    {"Classification": 4, "PINN": 2, "SR distillation": 3, "EML cost": 3},
}


def print_profile_table(acts: list[ActivationProfile]) -> None:
    header = (
        f"{'Name':10} {'Cost':8} {'Vanish':8} {'Dying':7} "
        f"{'Smooth':8} {'PINN':6} {'Distil':7}"
    )
    print(header)
    print("-" * 65)
    for a in acts:
        cost_str = str(a.superbest_cost) + "n" if isinstance(a.superbest_cost, int) else str(a.superbest_cost)
        print(
            f"{a.name:10} {cost_str:8} {str(a.vanishing_gradient):8} "
            f"{str(a.dying_neuron):7} {str(a.smooth):8} "
            f"{str(a.pinn_suitable):6} {str(a.sr_distillable):7}"
        )


def print_suitability_grid() -> None:
    col_w = 16
    names = list(SUITABILITY.keys())
    print(f"{'Task':20}", end="")
    for n in names:
        print(f"{n:>{col_w}}", end="")
    print()
    print("-" * (20 + col_w * len(names)))
    for task in TASK_FAMILIES:
        print(f"{task:20}", end="")
        for n in names:
            rating = SUITABILITY[n][task]
            bar = "█" * rating + "░" * (5 - rating)
            print(f"{bar:>{col_w}}", end="")
        print()


def print_headline_findings() -> None:
    print()
    print("HEADLINE FINDINGS")
    print("-" * 60)
    print()
    print("1. softplus = LEAd = 1n EML primitive")
    print("   softplus(x) = ln(1 + exp(x)) is exactly the LEAd operator.")
    print("   Cost: 1n. Gradient: sigmoid(x) ∈ (0,1) always.")
    print("   → No vanishing gradient. No dead neurons. Fully distillable.")
    print()
    print("2. ReLU wins classification, fails EML distillation")
    print("   max(0,x) is not in the EML operator closure (piecewise linear).")
    print("   Dead neurons (dying ReLU) are survivable with SGD + batch norm")
    print("   on classification tasks, but catastrophic for PDE residuals.")
    print()
    print("3. Why softplus wins on PINNs")
    print("   Physics equations are built from exp, ln, trig — the same primitives")
    print("   as EML operators. When the network uses softplus activations, each")
    print("   hidden layer IS an EML transformation. The symbolic head can then")
    print("   distil the full DNN into a closed-form EML expression.")
    print("   Example: Arrhenius law A·exp(-Ea/RT) needs only DEML route → 5n total.")
    print()
    print("4. GELU is the transformer workhorse but EML-opaque")
    print("   erf(x) is not in the EML closure. No finite EML tree represents GELU.")
    print("   The tanh approximation to GELU needs ~30n — too expensive.")
    print()
    print("5. Cost ranking (lower = cheaper):")
    for a in sorted(ACTIVATIONS, key=lambda x: x.superbest_cost if isinstance(x.superbest_cost, int) else 999):
        cost = str(a.superbest_cost) + "n" if isinstance(a.superbest_cost, int) else str(a.superbest_cost)
        print(f"   {a.name:10} {cost}")


if __name__ == "__main__":
    print("=" * 70)
    print("NN-7: Activation Function Shootout — Mathematical Analysis")
    print("=" * 70)
    print()

    print("Activation profile table:")
    print()
    print_profile_table(ACTIVATIONS)

    print()
    print("EML routes for each activation:")
    print()
    for a in ACTIVATIONS:
        cost = str(a.superbest_cost) + "n" if isinstance(a.superbest_cost, int) else str(a.superbest_cost)
        print(f"  {a.name} ({a.formula})")
        print(f"    SuperBEST cost: {cost}")
        print(f"    Gradient: {a.gradient_formula}")
        print(f"    {a.notes[:120]}...")
        print()

    print("Suitability grid (5=best, 1=worst, ░░░░░ = rating bars):")
    print()
    print_suitability_grid()

    print_headline_findings()

    print()
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print()
    print("For EML/DEML/LEAd hybrid DNN+symbolic architectures:")
    print("  Activation: softplus (= LEAd = 1n)")
    print("  Why: network layers ARE EML transformations; distillation is exact.")
    print()
    print("For pure classification (no symbolic distillation goal):")
    print("  Activation: ReLU or GELU")
    print("  Why: maximum gradient flow; proven on ImageNet/CIFAR benchmarks.")
    print()
    print("Operator subset sweet spot: {EML, DEML, LEAd}")
    print("  — gradient stable, softplus native, covers exp(-x) and ln(1+exp(x))")
