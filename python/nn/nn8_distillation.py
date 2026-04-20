#!/usr/bin/env python3
# encoding: utf-8
"""
NN-8: Expression Distillation Analysis.

For each target function, compute:
  - Exact SuperBEST v4 cost
  - Success/failure prediction based on completeness theory
  - Compression ratio: DNN parameters vs EML nodes
  - Whether EML completeness theorem guarantees a solution exists

SuperBEST v4 costs:
  exp=1n, ln=1n, recip=1n, neg=2n, mul=2n, sub=2n, div=2n,
  sqrt=2n, pow=3n, add_pos=3n, add_gen=11n

Completeness reference (NN-9 / monogate completeness theory):
  EML is complete for functions built from {exp, ln, *, /, -, +}
  EML is INCOMPLETE for: sin, cos, step functions, polynomials with large N.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


COSTS: dict[str, int] = {
    "exp": 1, "ln": 1, "recip": 1, "neg": 2, "mul": 2,
    "sub": 2, "div": 2, "sqrt": 2, "pow": 3, "add_pos": 3, "add_gen": 11,
}


def eml_cost(breakdown: dict[str, int]) -> int:
    return sum(COSTS[op] * cnt for op, cnt in breakdown.items())


@dataclass(frozen=True)
class DistillationTarget:
    name: str
    formula: str
    domain: str                        # domain of validity
    cost_breakdown: dict[str, int]
    eml_nodes: int                     # number of EML operator nodes
    eml_cost_total: int                # SuperBEST cost in n-units
    completeness_status: str           # "COMPLETE" | "INCOMPLETE" | "APPROXIMATE"
    distillation_prediction: str       # "SUCCESS" | "FAILS" | "APPROXIMATE"
    failure_reason: Optional[str]      # None if success predicted
    # Compression ratio: approximate DNN params for similar accuracy / EML nodes
    dnn_params_estimate: int
    eml_node_count: int
    compression_note: str
    notes: str


TARGETS: list[DistillationTarget] = [
    DistillationTarget(
        name="Arrhenius",
        formula="A * exp(-Ea / (R*T))",
        domain="T > 0, thermochemistry",
        cost_breakdown={"neg": 1, "mul": 2, "div": 1},   # DEML route + mul for A
        eml_nodes=5,
        eml_cost_total=1 + eml_cost({"mul": 2, "div": 1}),  # DEML=1n + 2*2 + 2 = 7n → but neg+div+mul = 2+2+2 = 6, DEML = 1 → 7
        completeness_status="COMPLETE",
        distillation_prediction="SUCCESS",
        failure_reason=None,
        dnn_params_estimate=500,    # small MLP for T→rate
        eml_node_count=5,
        compression_note="500 params → 5 EML nodes: 100:1 compression",
        notes=(
            "A·exp(-Ea/RT). "
            "DEML(Ea/(R*T), A_placeholder): the inner term Ea/(R*T) = div(Ea, mul(R,T)). "
            "SuperBEST route: mul(R,T)=2n, div(Ea, RT)=2n, DEML applied=1n, "
            "mul(A, result) would be adding A as a scale=2n. "
            "Exact total: mul(R,T) + div(Ea,RT) + exp_neg route + A*... "
            "Simplified: 5 operator nodes, cost ≈ 7n. "
            "This is the canonical PINN distillation success case: "
            "the physics IS an EML expression. "
            "Expected compression: ~100:1 (500 DNN params → 5 EML nodes)."
        ),
    ),
    DistillationTarget(
        name="sigmoid",
        formula="1 / (1 + exp(-x))",
        domain="x ∈ ℝ",
        cost_breakdown={"neg": 1, "exp": 1, "add_pos": 1, "recip": 1},
        eml_nodes=4,
        eml_cost_total=eml_cost({"neg": 1, "exp": 1, "add_pos": 1, "recip": 1}),  # 2+1+3+1 = 7n
        completeness_status="COMPLETE",
        distillation_prediction="SUCCESS",
        failure_reason=None,
        dnn_params_estimate=200,
        eml_node_count=4,
        compression_note="200 params → 4 EML nodes: 50:1 compression",
        notes=(
            "1/(1+exp(-x)). "
            "Route: neg(x)=2n, exp(neg_x)=1n, add_pos(1, exp_neg_x)=3n, recip=1n. "
            "Total: 7n, 4 operator nodes. "
            "Sigmoid IS in the EML closure — it is built purely from exp, recip, and addition. "
            "Distillation will converge to the exact 7n expression. "
            "This is a key validation target: train a network to compute sigmoid, "
            "then distil — should recover exact formula."
        ),
    ),
    DistillationTarget(
        name="polynomial_x3_x",
        formula="x^3 + x",
        domain="x ∈ ℝ",
        cost_breakdown={"pow": 1, "add_gen": 1},
        eml_nodes=2,
        eml_cost_total=eml_cost({"pow": 1, "add_gen": 1}),  # 3 + 11 = 14n
        completeness_status="COMPLETE",
        distillation_prediction="SUCCESS",
        failure_reason=None,
        dnn_params_estimate=300,
        eml_node_count=2,
        compression_note="300 params → 14n (2 nodes): expensive but achievable",
        notes=(
            "x^3 + x. "
            "pow(x,3)=3n, add_gen(x^3, x)=11n. Total: 14n. "
            "Technically in EML closure (pow and add_gen are valid operators). "
            "HOWEVER: add_gen=11n makes this the most expensive 2-node expression. "
            "Distillation SUCCEEDS theoretically but is costly. "
            "Practically: the search space is wide because add_gen has 11 sub-operators. "
            "A wider-domain polynomial (Nguyen-1: x^3+x^2+x = 28n) becomes very hard "
            "to distil efficiently; this 2-term version is the borderline case."
        ),
    ),
    DistillationTarget(
        name="sin_x",
        formula="sin(x)",
        domain="x ∈ ℝ",
        cost_breakdown={},   # no finite EML representation
        eml_nodes=0,
        eml_cost_total=0,
        completeness_status="INCOMPLETE",
        distillation_prediction="FAILS",
        failure_reason=(
            "sin(x) has infinitely many zeros (at x = nπ for all n∈ℤ). "
            "EML expressions eml(x,y) = exp(x) - ln(y) can only have zeros where "
            "exp(x) = ln(y), which is a smooth curve in the plane, not a discrete "
            "infinite set on the real line. "
            "Therefore no finite EML tree can represent sin(x) exactly. "
            "The infinite-zeros barrier is an incompleteness theorem result. "
            "Approximate distillation to a partial-range Taylor truncation is possible "
            "but loses accuracy outside the training interval."
        ),
        dnn_params_estimate=400,
        eml_node_count=0,
        compression_note="N/A — distillation fails; approximation only over bounded interval",
        notes=(
            "sin(x) is NOT in the EML closure. "
            "The monogate completeness characterization proves: "
            "any EML expression f(x) has at most finitely many real zeros "
            "(because exp(g(x)) = ln(h(x)) has isolated solutions). "
            "sin(x) has infinitely many zeros — contradiction. "
            "CEML (complex EML) can represent sin via Euler's formula: "
            "sin(x) = Im(exp(ix)) — but this requires complex arithmetic "
            "outside the real-valued EML framework. "
            "Practical outcome: distillation loop will find a best-fit rational/exp "
            "approximation but will not converge to an exact closed form."
        ),
    ),
    DistillationTarget(
        name="ReLU",
        formula="max(0, x)",
        domain="x ∈ ℝ",
        cost_breakdown={},
        eml_nodes=0,
        eml_cost_total=0,
        completeness_status="INCOMPLETE",
        distillation_prediction="FAILS",
        failure_reason=(
            "ReLU is piecewise linear with a non-smooth kink at x=0. "
            "EML expressions are C-infinity smooth (exp and ln are analytic). "
            "A C-infinity function cannot equal a non-smooth function on any open interval. "
            "Therefore no finite EML tree can represent ReLU exactly. "
            "Approximation: softplus(kx)/k → ReLU as k→∞, but this is a limit, "
            "not a finite EML expression."
        ),
        dnn_params_estimate=100,
        eml_node_count=0,
        compression_note="N/A — distillation fails; discontinuity not EML-representable",
        notes=(
            "ReLU = max(0, x) is not in the EML operator closure. "
            "Proof: all EML expressions are smooth (C-∞) because exp and ln are analytic. "
            "ReLU has a non-differentiable point at x=0; no smooth function equals ReLU "
            "on an open set containing 0. "
            "This is the primary reason to avoid ReLU in EML hybrid architectures: "
            "the trunk cannot be distilled if it uses ReLU activations. "
            "Use softplus (= LEAd = 1n) instead for distillable architectures."
        ),
    ),
]


# ── Compression ratio table ───────────────────────────────────────────────────
def print_compression_table(targets: list[DistillationTarget]) -> None:
    header = f"{'Target':22} {'Prediction':12} {'EML cost':10} {'DNN params':12} {'Compression'}"
    print(header)
    print("-" * 75)
    for t in targets:
        cost_str = f"{t.eml_cost_total}n" if t.eml_cost_total > 0 else "N/A"
        pred = t.distillation_prediction
        ratio = (
            f"~{t.dnn_params_estimate // max(t.eml_node_count, 1)}:1"
            if t.eml_node_count > 0
            else "N/A"
        )
        print(
            f"{t.name:22} {pred:12} {cost_str:10} "
            f"{str(t.dnn_params_estimate) + ' params':12} {ratio}"
        )


def print_failure_analysis(targets: list[DistillationTarget]) -> None:
    failures = [t for t in targets if t.distillation_prediction == "FAILS"]
    print(f"\nDistillation FAILURES ({len(failures)} targets):")
    for t in failures:
        print(f"\n  [{t.name}]  {t.formula}")
        print(f"  Status: {t.completeness_status}")
        print(f"  Reason: {t.failure_reason}")


def print_success_analysis(targets: list[DistillationTarget]) -> None:
    successes = [t for t in targets if t.distillation_prediction == "SUCCESS"]
    print(f"\nDistillation SUCCESSES ({len(successes)} targets):")
    for t in successes:
        print(f"\n  [{t.name}]  {t.formula}")
        print(f"  EML cost: {t.eml_cost_total}n  ({t.eml_node_count} operator nodes)")
        print(f"  Compression: {t.compression_note}")
        cost_breakdown_str = ", ".join(
            f"{op}×{cnt}={COSTS[op]*cnt}n" for op, cnt in t.cost_breakdown.items()
        )
        print(f"  Breakdown: {cost_breakdown_str}")


if __name__ == "__main__":
    print("=" * 75)
    print("NN-8: Expression Distillation Analysis")
    print("=" * 75)
    print()
    print("Target: train a DNN to approximate each function,")
    print("then apply EML symbolic distillation and predict success/failure.\n")

    print_compression_table(TARGETS)

    print_success_analysis(TARGETS)
    print_failure_analysis(TARGETS)

    print()
    print("=" * 75)
    print("COMPLETENESS SUMMARY")
    print("=" * 75)
    print()
    print("EML is COMPLETE for functions built from: {exp, ln, *, /, -, +, recip}")
    print("EML is INCOMPLETE for:")
    print("  - Piecewise functions (ReLU, absolute value, step)")
    print("    Reason: EML expressions are C-∞ smooth; kinks are not representable.")
    print("  - Functions with infinitely many zeros (sin, cos, any periodic function)")
    print("    Reason: EML zeros are isolated; infinite-zero sets are impossible.")
    print()
    print("Practical rule for EML distillation pipeline:")
    print("  IF target ∈ {exp, ln, rational, power combinations} → distil with EML.")
    print("  IF target involves trig or piecewise → use CEML (complex) or abandon.")
    print()
    print("SuperBEST v4 cost reference:")
    for op, cost in COSTS.items():
        print(f"  {op:10} = {cost}n")
