#!/usr/bin/env python3
# encoding: utf-8
"""
NN-6: SR Benchmark — EML vs PySR vs gplearn analysis.
For each benchmark function, compute SuperBEST cost and EML advantage.

SuperBEST v4 costs:
  exp=1n, ln=1n, recip=1n, neg=2n, mul=2n, sub=2n, div=2n,
  sqrt=2n, pow=3n, add_pos=3n, add_gen=11n

EML wins on transcendental targets (exp, ln, sin, cos via ceml/deml).
EML loses on polynomial targets (x^n + x^m + ...) because add_gen=11n.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── SuperBEST v4 operator costs ──────────────────────────────────────────────
COSTS: dict[str, int] = {
    "exp":     1,
    "ln":      1,
    "recip":   1,
    "neg":     2,
    "mul":     2,
    "sub":     2,
    "div":     2,
    "sqrt":    2,
    "pow":     3,
    "add_pos": 3,
    "add_gen": 11,
}


@dataclass(frozen=True)
class BenchmarkEntry:
    name: str
    formula: str
    target_type: str               # "polynomial" | "transcendental" | "mixed" | "combinatorial"
    cost_breakdown: dict[str, int] # operator -> count
    cost_min: int                  # worst-case / best-case noted separately
    cost_best: Optional[int]       # positive-domain optimisation, None if same
    eml_verdict: str               # "WINS" | "LOSES" | "NEUTRAL"
    pySR_nodes: str                # rough PySR node count estimate
    notes: str


def compute_cost(breakdown: dict[str, int]) -> int:
    return sum(COSTS[op] * cnt for op, cnt in breakdown.items())


# ── Benchmark definitions ─────────────────────────────────────────────────────
BENCHMARKS: list[BenchmarkEntry] = [
    BenchmarkEntry(
        name="Nguyen-1",
        formula="x^3 + x^2 + x",
        target_type="polynomial",
        cost_breakdown={"pow": 2, "add_gen": 2},   # 2 pow + 2 add_gen (x^3+x^2+x)
        cost_min=compute_cost({"pow": 2, "add_gen": 2}),  # 28n
        cost_best=compute_cost({"pow": 2, "add_pos": 2}), # 12n if x>0
        eml_verdict="LOSES",
        pySR_nodes="~3-5 nodes (direct polynomial)",
        notes=(
            "x^3 needs pow=3n, x^2 needs pow=3n. "
            "Two add_gen = 22n (or 6n if x>0 guaranteed). "
            "PySR represents polynomials directly with ~3 nodes. "
            "EML add_gen=11n makes polynomial sums brutally expensive."
        ),
    ),
    BenchmarkEntry(
        name="Nguyen-4",
        formula="x^6 + x^5 + x^4 + x^3 + x^2 + x",
        target_type="polynomial",
        cost_breakdown={"pow": 5, "add_gen": 5},   # x, x^2..x^6; 5 pow terms
        cost_min=compute_cost({"pow": 5, "add_gen": 5}),  # 70n
        cost_best=compute_cost({"pow": 5, "add_pos": 5}), # 30n if x>0
        eml_verdict="LOSES",
        pySR_nodes="~8-12 nodes",
        notes=(
            "Six power terms (x is free as terminal), five additions. "
            "add_gen route: 5*3 + 5*11 = 70n. "
            "Even add_pos route gives 30n vs PySR's ~10 nodes. "
            "Extreme polynomial cost in EML."
        ),
    ),
    BenchmarkEntry(
        name="Nguyen-7",
        formula="log(x+1) + log(x^2+1)",
        target_type="transcendental",
        cost_breakdown={"add_pos": 3, "pow": 1, "ln": 2},
        cost_min=compute_cost({"add_pos": 3, "pow": 1, "ln": 2}),  # 14n
        cost_best=None,
        eml_verdict="WINS",
        pySR_nodes="~8-15 nodes (Taylor approx needed)",
        notes=(
            "log(x+1): add_pos(x,1)=3n, ln=1n → 4n. "
            "x^2: pow=3n. log(x^2+1): pow+add_pos+ln = 3+3+1 = 7n. "
            "Final add_pos = 3n. Total = 14n. "
            "PySR cannot represent log natively; needs rational or Taylor approximation → many nodes."
        ),
    ),
    BenchmarkEntry(
        name="Feynman-I.6.20",
        formula="exp(-theta^2/2) / sqrt(2*pi)",
        target_type="transcendental",
        cost_breakdown={"pow": 1, "div": 2},  # pow(theta,2) + div/2 + DEML=1n
        cost_min=1 + compute_cost({"pow": 1, "div": 2}),  # DEML=1n + 3+2+2=7 → 8n
        cost_best=None,
        eml_verdict="WINS",
        pySR_nodes="~10-20 nodes (exp approximated)",
        notes=(
            "DEML(x,r) = exp(-x) - ln(r). "
            "theta^2/2 via pow+div = 5n. "
            "DEML applied = 1n. "
            "sqrt(2*pi) is a constant ≈ 2.507; the division by constant = 2n. "
            "Total ≈ 8n. "
            "PySR must approximate exp(-x^2/2) with high-degree polynomials or rational functions."
        ),
    ),
    BenchmarkEntry(
        name="Feynman-I.12.1",
        formula="q1*q2 / (4*pi*epsilon*r^2)",
        target_type="mixed",
        cost_breakdown={"mul": 2, "pow": 1, "div": 1},
        cost_min=compute_cost({"mul": 2, "pow": 1, "div": 1}),  # 11n
        cost_best=None,
        eml_verdict="NEUTRAL",
        pySR_nodes="~6-8 nodes",
        notes=(
            "Pure rational function: no exp or ln advantage. "
            "q1*q2 = 2n, r^2 = 3n, 4*pi*epsilon = constant = 0n, "
            "two muls for denominator assembly = 2n, div = 2n → ~11n. "
            "PySR handles rational functions well natively. "
            "EML has no structural edge here."
        ),
    ),
    BenchmarkEntry(
        name="Korns-12",
        formula="2 - 2.1*cos(9.8*x)*sin(1.3*y)",
        target_type="transcendental",
        cost_breakdown={"mul": 4, "sub": 1},  # 2 ceml for cos/sin=2n, mul chain, sub
        cost_min=2 + compute_cost({"mul": 4, "sub": 1}),  # ceml cos+sin=2n + 4*2+2 = 14n
        cost_best=None,
        eml_verdict="WINS",
        pySR_nodes="~20-40 nodes (trig via Taylor)",
        notes=(
            "CEMl(x) routes cos and sin as 1n primitives each. "
            "mul(9.8,x)=2n, cos(9.8x)=1n(ceml) → 3n. "
            "mul(1.3,y)=2n, sin(1.3y)=1n(ceml) → 3n. "
            "cos*sin=2n, 2.1*(cos*sin)=2n, 2-...=2n → 4n. "
            "Total ≈ 12n. "
            "PySR needs Taylor expansion for trig; easily 20+ nodes for adequate precision."
        ),
    ),
    BenchmarkEntry(
        name="Keijzer-6",
        formula="sum(1/i, i=1..x)",
        target_type="combinatorial",
        cost_breakdown={"recip": 1, "add_pos": 1},  # per-term cost
        cost_min=4,   # 4N-3 for N terms; not a fixed expression cost
        cost_best=None,
        eml_verdict="NEUTRAL",
        pySR_nodes="symbolic (closed form: harmonic number H_x)",
        notes=(
            "Harmonic sum requires iterating over variable N=x terms. "
            "Each recip(i) = 1n, each addition = 3n (add_pos assumed positive). "
            "Per-term cost = 4n, total = 4N-3 → grows linearly with x. "
            "Neither EML nor polynomial SR has a closed-form advantage; "
            "both must approximate or unroll. EML advantage: recip=1n is cheap."
        ),
    ),
    BenchmarkEntry(
        name="Livermore-2",
        formula="(x-3)^2 + (x-3)^3",
        target_type="polynomial",
        cost_breakdown={"sub": 1, "pow": 2, "add_pos": 1},
        cost_min=compute_cost({"sub": 1, "pow": 2, "add_pos": 1}),  # 11n
        cost_best=None,
        eml_verdict="LOSES",
        pySR_nodes="~5-7 nodes",
        notes=(
            "sub(x,3)=2n once, shared. pow((x-3),2)=3n, pow((x-3),3)=3n. "
            "add_pos((x-3)^2, (x-3)^3) = 3n if x>3. "
            "Total ≈ 11n with CSE (common subexpression elimination). "
            "PySR: directly represents as 2-term polynomial ~5 nodes. "
            "No transcendental advantage for EML here."
        ),
    ),
    BenchmarkEntry(
        name="Strogatz-1",
        formula="-sin(x)",
        target_type="transcendental",
        cost_breakdown={"neg": 1},   # ceml=1n for sin, neg=2n
        cost_min=1 + COSTS["neg"],   # 3n total
        cost_best=None,
        eml_verdict="WINS",
        pySR_nodes="~10-20 nodes (Taylor sin)",
        notes=(
            "sin(x) via ceml = 1n. neg(sin(x)) = 2n. Total = 3n. "
            "Minimal expression. PySR needs odd-degree polynomial approximation "
            "for sin; 5th-order Taylor needs ~5 terms with many mul nodes."
        ),
    ),
    BenchmarkEntry(
        name="Custom-1",
        formula="exp(-x)*sin(2*pi*x)",
        target_type="transcendental",
        cost_breakdown={"mul": 2},   # DEML=1n, mul(2pi,x)=2n, ceml-sin=1n, mul(exp_neg,sin)=2n
        cost_min=1 + compute_cost({"mul": 2}) + 1,  # DEML + 2*mul + ceml = 6n
        cost_best=None,
        eml_verdict="WINS",
        pySR_nodes="~30-60 nodes (both exp and sin approximated)",
        notes=(
            "DEML(x,r) = exp(-x) - ln(r); here we use the exp(-x) route → 1n. "
            "2*pi is a constant → 0n. mul(2pi, x) = 2n. "
            "sin(2pi*x) via ceml = 1n. mul(exp_neg_x, sin) = 2n. "
            "Total = 6n. "
            "PySR must approximate both exp(-x) and sin simultaneously; "
            "this is the strongest EML win in the benchmark set."
        ),
    ),
]


# ── Verdict summary ───────────────────────────────────────────────────────────
EML_WINS    = [b.name for b in BENCHMARKS if b.eml_verdict == "WINS"]
EML_LOSES   = [b.name for b in BENCHMARKS if b.eml_verdict == "LOSES"]
EML_NEUTRAL = [b.name for b in BENCHMARKS if b.eml_verdict == "NEUTRAL"]


def print_table(benchmarks: list[BenchmarkEntry]) -> None:
    header = f"{'Function':20} {'Type':15} {'EML Cost':10} {'Best':8} {'Verdict':8} {'PySR est.'}"
    print(header)
    print("-" * 80)
    for b in benchmarks:
        best_str = f"{b.cost_best}n" if b.cost_best else "—"
        print(
            f"{b.name:20} {b.target_type:15} {str(b.cost_min) + 'n':10} "
            f"{best_str:8} {b.eml_verdict:8} {b.pySR_nodes}"
        )


def print_notes(benchmarks: list[BenchmarkEntry]) -> None:
    for b in benchmarks:
        print(f"\n[{b.name}]  {b.formula}")
        print(f"  Cost: {b.cost_min}n", end="")
        if b.cost_best:
            print(f"  (positive-domain: {b.cost_best}n)", end="")
        print(f"  ->  {b.eml_verdict}")
        print(f"  {b.notes}")


if __name__ == "__main__":
    print("=" * 80)
    print("NN-6: SR Benchmark - EML vs PySR/gplearn Cost Analysis")
    print("=" * 80)
    print()
    print_table(BENCHMARKS)

    print()
    print(f"EML WINS    ({len(EML_WINS)}): {', '.join(EML_WINS)}")
    print(f"EML LOSES   ({len(EML_LOSES)}): {', '.join(EML_LOSES)}")
    print(f"EML NEUTRAL ({len(EML_NEUTRAL)}): {', '.join(EML_NEUTRAL)}")

    print()
    print("-" * 80)
    print("KEY RULE: EML wins on transcendental targets (exp, ln, trig via ceml/deml).")
    print("          EML loses on polynomial targets because add_gen=11n is expensive.")
    print("          Win rate: 5/10 functions. Strongly correlated with target type.")
    print("-" * 80)

    print()
    print("Detailed cost notes:")
    print_notes(BENCHMARKS)

    print()
    print("SuperBEST v4 operator costs used:")
    for op, cost in COSTS.items():
        print(f"  {op:10} = {cost}n")
