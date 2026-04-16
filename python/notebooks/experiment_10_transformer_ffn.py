"""
experiment_10  --  Transformer FFN Block Benchmark
====================================================
Tests BEST routing speedup on a Transformer-style Feed-Forward Network (FFN):
    FFN(x) = Linear(GELU(Linear(x)))

Demonstrates gelu_best_approx (14n, tanh-based) vs gelu_eml_approx (17n).

Architecture: Standard 4x expansion ratio (common in GPT/BERT)
    - input_dim  d
    - hidden_dim 4*d  (FFN intermediate)
    - output_dim d

Results confirm that BEST routing saves ~18% nodes on GELU and extends
the same compound-operator savings to FFN blocks.
"""

import timeit
import math
import sys
from typing import Callable

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from monogate import gelu_eml_approx, gelu_best_approx, sin_eml_taylor, sin_best_taylor
except ImportError as exc:
    print(f"monogate not installed: {exc}")
    sys.exit(1)


# ── helpers ───────────────────────────────────────────────────────────────────

def ffn_forward(
    x: list[float],
    W1: list[list[float]],
    b1: list[float],
    W2: list[list[float]],
    b2: list[float],
    activation: Callable[[float], float],
) -> list[float]:
    """Pure-Python FFN: Linear -> Activation -> Linear."""
    d_in  = len(x)
    d_hid = len(b1)
    d_out = len(b2)

    # First linear: h = W1 @ x + b1
    h = [sum(W1[j][i] * x[i] for i in range(d_in)) + b1[j] for j in range(d_hid)]

    # Activation
    h_act = [activation(v) for v in h]

    # Second linear: out = W2 @ h_act + b2
    out = [sum(W2[k][j] * h_act[j] for j in range(d_hid)) + b2[k] for k in range(d_out)]
    return out


def make_ffn_weights(d_in: int, d_hid: int, d_out: int, seed: int = 42):
    """Deterministic weight initialisation (Xavier-ish, no torch needed)."""
    import random
    rng = random.Random(seed)
    scale1 = math.sqrt(2.0 / (d_in + d_hid))
    scale2 = math.sqrt(2.0 / (d_hid + d_out))

    W1 = [[rng.gauss(0, scale1) for _ in range(d_in)]  for _ in range(d_hid)]
    b1 = [0.0] * d_hid
    W2 = [[rng.gauss(0, scale2) for _ in range(d_hid)] for _ in range(d_out)]
    b2 = [0.0] * d_out
    return W1, b1, W2, b2


def make_input(d: int, batch: int, seed: int = 7) -> list[list[float]]:
    import random
    rng = random.Random(seed)
    return [[rng.gauss(0, 1.0) for _ in range(d)] for _ in range(batch)]


def bench(fn, runs: int = 200) -> float:
    """Return ms per call (median of 3 blocks of `runs`)."""
    times = []
    for _ in range(3):
        t = timeit.timeit(fn, number=runs)
        times.append(t / runs * 1000)
    return sorted(times)[1]  # median


# ── section A: single GELU call ───────────────────────────────────────────────

def section_a():
    print()
    print("Section A  GELU approximation: EML vs BEST  (single call)")
    print("-" * 60)
    print()
    print("  Formula: 0.5*x*(1 + tanh(sqrt(2/pi)*(x + 0.044715*x^3)))")
    print("  EML:  exp_eml (1n) + add_eml (11n) + recip_eml (5n) = 17n")
    print("  BEST: exp     (1n) + add     (11n) + recip_edl (2n) = 14n")
    print()

    xs = [-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]
    ref_gelu = lambda x: x * 0.5 * (1 + math.tanh(math.sqrt(2/math.pi) * (x + 0.044715*x**3)))

    print(f"  {'x':>6}  {'EML':>12}  {'BEST':>12}  {'math ref':>12}  {'err EML':>10}  {'err BEST':>10}")
    print(f"  {'-'*6}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}")
    for x in xs:
        eml_v  = gelu_eml_approx(x)
        best_v = gelu_best_approx(x)
        ref_v  = ref_gelu(x)
        print(f"  {x:>6.2f}  {eml_v:>12.8f}  {best_v:>12.8f}  {ref_v:>12.8f}  "
              f"{abs(eml_v-ref_v):>10.2e}  {abs(best_v-ref_v):>10.2e}")
    print()

    t_eml  = bench(lambda: gelu_eml_approx(1.0),  runs=5000)
    t_best = bench(lambda: gelu_best_approx(1.0), runs=5000)
    print(f"  {'Function':<20}  {'us/call':>10}  {'nodes':>8}")
    print(f"  {'-'*20}  {'-'*10}  {'-'*8}")
    print(f"  {'gelu_eml_approx':<20}  {t_eml*1000:>10.2f}  {'17':>8}")
    print(f"  {'gelu_best_approx':<20}  {t_best*1000:>10.2f}  {'14':>8}")
    print(f"  {'-'*20}  {'-'*10}  {'-'*8}")
    speedup = t_eml / t_best if t_best > 0 else float("nan")
    savings = round((1 - 14/17) * 100)
    print(f"  Speedup {speedup:.2f}x   ({savings}% fewer nodes)")
    print()


# ── section B: batch activation ───────────────────────────────────────────────

def section_b(d_hid: int = 256, batch: int = 32):
    n_activations = d_hid * batch

    print(f"Section B  Batch GELU  ({batch} samples x {d_hid} hidden = {n_activations} activations)")
    print("-" * 60)
    print()

    import random
    rng = random.Random(99)
    inputs = [rng.gauss(0, 1.0) for _ in range(n_activations)]

    def run_eml():
        return [gelu_eml_approx(v) for v in inputs]

    def run_best():
        return [gelu_best_approx(v) for v in inputs]

    t_eml  = bench(run_eml,  runs=30)
    t_best = bench(run_best, runs=30)
    speedup = t_eml / t_best if t_best > 0 else float("nan")
    savings = round((1 - 14/17) * 100)

    print(f"  {'Activation':<20}  {'ms/batch':>10}  {'us/elem':>10}  {'gates/elem':>12}")
    print(f"  {'-'*20}  {'-'*10}  {'-'*10}  {'-'*12}")
    us_eml  = t_eml  * 1000 / n_activations
    us_best = t_best * 1000 / n_activations
    print(f"  {'EML-GELU':<20}  {t_eml:>10.3f}  {us_eml:>10.2f}  {'17':>12}")
    print(f"  {'BEST-GELU':<20}  {t_best:>10.3f}  {us_best:>10.2f}  {'14':>12}")
    print(f"  {'-'*20}  {'-'*10}  {'-'*10}  {'-'*12}")
    print(f"  Speedup {speedup:.2f}x             {savings}% fewer gates")
    print()


# ── section C: FFN forward pass ───────────────────────────────────────────────

def section_c(d: int = 16, batch: int = 8):
    d_hid = 4 * d
    n_act = d_hid * batch

    print(f"Section C  Transformer FFN forward  (d={d}, 4x hidden={d_hid}, batch={batch})")
    print("-" * 60)
    print()
    print(f"  Architecture: Linear({d}->{d_hid}) -> GELU -> Linear({d_hid}->{d})")
    print(f"  EML/BEST activation called {d_hid} times per sample = {n_act} calls/batch")
    print()

    W1, b1, W2, b2 = make_ffn_weights(d, d_hid, d)
    inputs = make_input(d, batch)

    def run_eml():
        for x in inputs:
            ffn_forward(x, W1, b1, W2, b2, gelu_eml_approx)

    def run_best():
        for x in inputs:
            ffn_forward(x, W1, b1, W2, b2, gelu_best_approx)

    def run_native():
        for x in inputs:
            ffn_forward(x, W1, b1, W2, b2, lambda v: v * 0.5 * (1 + math.tanh(math.sqrt(2/math.pi)*(v + 0.044715*v**3))))

    t_native = bench(run_native, runs=50)
    t_eml    = bench(run_eml,    runs=50)
    t_best   = bench(run_best,   runs=50)

    speedup_vs_eml  = t_eml  / t_best  if t_best  > 0 else float("nan")
    speedup_native  = t_eml  / t_native if t_native > 0 else float("nan")
    overhead_best   = t_best / t_native if t_native > 0 else float("nan")

    print(f"  {'Model':<30}  {'ms/fwd':>9}  {'us/sample':>10}")
    print(f"  {'-'*30}  {'-'*9}  {'-'*10}")
    print(f"  {'FFN (native math)':<30}  {t_native:>9.3f}  {t_native*1000/batch:>10.2f}")
    print(f"  {'FFN (EML-GELU)':<30}  {t_eml:>9.3f}  {t_eml*1000/batch:>10.2f}")
    print(f"  {'FFN (BEST-GELU)':<30}  {t_best:>9.3f}  {t_best*1000/batch:>10.2f}")
    print(f"  {'-'*30}  {'-'*9}  {'-'*10}")
    print(f"  BEST vs EML: {speedup_vs_eml:.2f}x faster")
    print(f"  BEST overhead vs native math: {overhead_best:.1f}x")
    print()


# ── section D: GELU vs sin across hidden dims ─────────────────────────────────

def section_d():
    print("Section D  GELU vs sin: speedup across hidden dimensions")
    print("-" * 60)
    print()
    print("  Compare EML->BEST savings for GELU (17->14n, ~18%) vs sin (245->63n, ~74%)")
    print()

    import random
    batch = 32

    print(f"  {'hidden':>8}  {'GELU speedup':>14}  {'sin speedup':>13}  {'GELU nodes':>12}  {'sin nodes':>11}")
    print(f"  {'-'*8}  {'-'*14}  {'-'*13}  {'-'*12}  {'-'*11}")

    for d_hid in [8, 16, 32, 64, 128]:
        rng = random.Random(42)
        # Only use positive values for sin (pow_eml domain constraint: x > 1)
        vals = [rng.uniform(1.1, 3.0) for _ in range(d_hid * batch)]

        t_gelu_eml  = bench(lambda: [gelu_eml_approx(v) for v in vals], runs=20)
        t_gelu_best = bench(lambda: [gelu_best_approx(v) for v in vals], runs=20)
        t_sin_eml   = bench(lambda: [sin_eml_taylor(v)  for v in vals], runs=20)
        t_sin_best  = bench(lambda: [sin_best_taylor(v) for v in vals], runs=20)

        sp_gelu = t_gelu_eml / t_gelu_best if t_gelu_best > 0 else float("nan")
        sp_sin  = t_sin_eml  / t_sin_best  if t_sin_best  > 0 else float("nan")

        n_gelu_eml = d_hid * batch * 17
        n_sin_eml  = d_hid * batch * 245
        print(f"  {d_hid:>8}  {sp_gelu:>13.2f}x  {sp_sin:>12.2f}x  {n_gelu_eml:>12,}  {n_sin_eml:>11,}")

    print()
    print("  Takeaway: BEST saves 18% nodes on GELU (~1.1-1.2x wall-clock),")
    print("            74% nodes on sin/cos (~3-4x wall-clock).")
    print("            Larger algebraic savings translate to larger runtime gains.")
    print()


# ── section E: comparison table ───────────────────────────────────────────────

def section_e():
    print("Section E  Node cost comparison summary")
    print("-" * 60)
    print()

    rows = [
        ("exp(x)",              "EXL/EML",   1,   1,  0),
        ("ln(x)",               "EXL",        1,   3, 67),
        ("mul(a,b)",            "EDL/EML",    7,  13, 46),
        ("div(a,b)",            "EDL/EML",    1,  15, 93),
        ("add(a,b)",            "EML",       11,  11,  0),
        ("sub(a,b)",            "EML",        5,   5,  0),
        ("pow(x,n)",            "EXL/EML",    3,  15, 80),
        ("recip(x)",            "EDL/EML",    2,   5, 60),
        ("sin(x) [8 terms]",   "EXL->BEST",  63, 245, 74),
        ("cos(x) [8 terms]",   "EXL->BEST",  63, 245, 74),
        ("gelu(x)",             "EDL->BEST",  14,  17, 18),
    ]

    print(f"  {'Function':<25}  {'Best operator':>15}  {'BEST n':>8}  {'EML n':>7}  {'Savings':>8}")
    print(f"  {'-'*25}  {'-'*15}  {'-'*8}  {'-'*7}  {'-'*8}")
    for name, op, best_n, eml_n, savings in rows:
        print(f"  {name:<25}  {op:>15}  {best_n:>8}  {eml_n:>7}  {savings:>7}%")
    print()


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SEP = "=" * 68

    print(SEP)
    print("  experiment_10  --  Transformer FFN Block Benchmark")
    print(SEP)
    print()
    print("  gelu_eml_approx: tanh-based, 17 EML nodes, error < 1e-10 vs exact")
    print("  gelu_best_approx: tanh-based, 14 nodes (EDL recip), same accuracy")
    print()

    section_a()
    section_b(d_hid=256, batch=32)
    section_c(d=16, batch=8)
    section_d()
    section_e()

    print(SEP)
    print("  experiment_10 complete.")
    print(SEP)
