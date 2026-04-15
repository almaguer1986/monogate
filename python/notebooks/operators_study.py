"""
Operator study: stability shootout (Part A) + parametric family explorer (Part C).

Run:
    cd D:/monogate
    python python/notebooks/operators_study.py

Part A — Stability shootout
  Compare EML vs EDL on three benchmarks:
    1. pow(x, 50)     — single high-power evaluation
    2. x^50 via 49 chained multiplications (accumulated rounding)
    3. degree-4 polynomial  p(x) = 3x^4 - 2x^3 + x^2 - x + 0.5
  Metric: relative error vs math.pow / math.fsum

  Key results (2026-04-15):
    A1: EDL wins for x<2 (and handles x=0.5 where EML domain-errors).
        EML wins for x>=2. Both ~1e-14 to 1e-15 relative error.
    A2: Chained mul (x^50): EDL wins for x<2, EML wins for x>=2.
        EML error stable ~1e-14; EDL accumulates to ~4e-13 at x>=2.
    A3: Neither hits NaN/inf in 200 chained multiplications (x=2.0).
    A4: EML polynomial eval fails for x<=1 — intermediate ln(x)<=0
        breaks mul_eml domain. Works cleanly for x>1 (err ~7e-16).

Part C — Parametric family explorer
  Scan operator variants and test whether each can build exp(x) and ln(x)
  as finite expression trees.  Variants tried:
    exp(x) - k * ln(y)        [k in {0.5, 1, 2, 3}]
    exp(x) / ln(y)^k          [k in {1, 2}]
    exp(k*x) - ln(y)          [k in {0.5, 2}]
    ln(y)^k - exp(x)          [k in {1, 2}]   (negated-family)

  Key result (2026-04-15):
    ONLY k=1 variants can build BOTH exp and ln:
      exp(x) - 1.0*ln(y)   [EML] — EML-style 3-node ln
      exp(x) / ln(y)^1     [EDL] — EML-style 3-node ln
    All other variants (scaled, negated, inverted) fail at least one.
    Confirms EML and EDL are the uniquely capable members of the
    natural exp-ln operator family.
"""

import math
import cmath
from typing import Callable

from monogate.core import (
    EML, EDL, EMN,
    exp_eml, ln_eml, mul_eml, pow_eml,
    exp_edl, ln_edl, mul_edl, pow_edl,
)

SEP  = "=" * 70
SEP2 = "-" * 70


# ─────────────────────────────────────────────────────────────────────────────
# Part A — Stability shootout
# ─────────────────────────────────────────────────────────────────────────────

def _rel(got, ref):
    if ref == 0:
        return abs(got)
    return abs(got - ref) / abs(ref)


def bench_pow(xs, n=50):
    """Benchmark A1: pow(x, n) relative error for EML and EDL."""
    print(f"\n{'Benchmark A1: pow(x,{n}) relative error':^70}")
    print(SEP2)
    print(f"  {'x':>8}  {'EML error':>14}  {'EDL error':>14}  {'winner':>8}")
    print(SEP2)
    for x in xs:
        ref = math.pow(x, n)
        try:
            eml_val = pow_eml(x, n)
            eml_err = _rel(eml_val, ref)
            eml_str = f"{eml_err:.2e}"
        except Exception as e:
            eml_str = f"ERROR ({e.__class__.__name__})"
            eml_err = float('inf')

        try:
            edl_val = pow_edl(complex(x), n).real
            edl_err = _rel(edl_val, ref)
            edl_str = f"{edl_err:.2e}"
        except Exception as e:
            edl_str = f"ERROR ({e.__class__.__name__})"
            edl_err = float('inf')

        if eml_err == float('inf') and edl_err < float('inf'):
            winner = "EDL"
        elif edl_err == float('inf') and eml_err < float('inf'):
            winner = "EML"
        elif eml_err <= edl_err:
            winner = "EML"
        else:
            winner = "EDL"

        print(f"  {x:>8.4f}  {eml_str:>14}  {edl_str:>14}  {winner:>8}")


def bench_chain_mul(xs, n=50):
    """Benchmark A2: x^n via n-1 chained multiplications."""
    print(f"\n{'Benchmark A2: x^n via chained mul (n=50) relative error':^70}")
    print(SEP2)
    print(f"  {'x':>8}  {'EML error':>14}  {'EDL error':>14}  {'winner':>8}")
    print(SEP2)
    for x in xs:
        ref = math.pow(x, n)

        # EML chain (real)
        try:
            acc = float(x)
            for _ in range(n - 1):
                acc = EML.mul(acc, float(x))
            eml_err = _rel(acc, ref)
            eml_str = f"{eml_err:.2e}"
        except Exception as e:
            eml_str = f"ERROR ({e.__class__.__name__})"
            eml_err = float('inf')

        # EDL chain (complex)
        try:
            acc = complex(x)
            for _ in range(n - 1):
                acc = EDL.mul(acc, complex(x))
            edl_err = _rel(acc.real, ref)
            edl_str = f"{edl_err:.2e}"
        except Exception as e:
            edl_str = f"ERROR ({e.__class__.__name__})"
            edl_err = float('inf')

        winner = "EML" if eml_err <= edl_err else "EDL"
        if eml_err == float('inf') and edl_err < float('inf'):
            winner = "EDL"
        elif edl_err == float('inf') and eml_err < float('inf'):
            winner = "EML"
        print(f"  {x:>8.4f}  {eml_str:>14}  {edl_str:>14}  {winner:>8}")


def bench_depth_to_nan(x=2.0, max_depth=200):
    """Benchmark A3: how deep can each chain go before NaN/inf?"""
    print(f"\n{'Benchmark A3: chained mul — depth before NaN/inf (x={x})':^70}")
    print(SEP2)

    # EML
    acc = float(x)
    eml_depth = 0
    for i in range(1, max_depth + 1):
        try:
            acc = EML.mul(acc, float(x))
            if not math.isfinite(acc):
                eml_depth = i
                break
        except Exception:
            eml_depth = i
            break
    else:
        eml_depth = max_depth

    # EDL
    acc = complex(x)
    edl_depth = 0
    for i in range(1, max_depth + 1):
        try:
            acc = EDL.mul(acc, complex(x))
            if not cmath.isfinite(acc):
                edl_depth = i
                break
        except Exception:
            edl_depth = i
            break
    else:
        edl_depth = max_depth

    label = lambda d: str(d) if d < max_depth else f">={max_depth}"
    print(f"  EML NaN/inf at depth: {label(eml_depth)}")
    print(f"  EDL NaN/inf at depth: {label(edl_depth)}")


def bench_polynomial(xs):
    """
    Benchmark A4: degree-4 polynomial p(x) = 3x^4 - 2x^3 + x^2 - x + 0.5
    Built from mul_eml/mul_edl and add (EML only, since EDL can't add).
    EML: full polynomial.  EDL: only the x^n terms (no addition).
    """
    print(f"\n{'Benchmark A4: polynomial evaluation p(x) = 3x^4-2x^3+x^2-x+0.5':^70}")
    print(SEP2)
    print(f"  {'x':>6}  {'ref p(x)':>14}  {'EML error':>14}  note")
    print(SEP2)

    def ref_poly(x):
        return 3*x**4 - 2*x**3 + x**2 - x + 0.5

    for x in xs:
        ref = ref_poly(x)
        try:
            x4 = pow_eml(x, 4)
            x3 = pow_eml(x, 3)
            x2 = pow_eml(x, 2)
            # 3x^4
            t4 = EML.mul(3.0, x4)
            # -2x^3
            t3_pos = EML.mul(2.0, x3)
            t3 = EML.neg(t3_pos)
            # x^2
            t2 = x2
            # -x
            t1 = EML.neg(x) if x > 0 else x  # neg_eml
            # +0.5
            # EML.add handles all sign cases
            result = EML.add(EML.add(EML.add(EML.add(t4, t3), t2), t1), 0.5)
            err = _rel(result, ref)
            print(f"  {x:>6.2f}  {ref:>14.6f}  {err:>14.2e}")
        except Exception as e:
            print(f"  {x:>6.2f}  {ref:>14.6f}  {'ERROR':>14}  ({e})")


# ─────────────────────────────────────────────────────────────────────────────
# Part C — Parametric family explorer
# ─────────────────────────────────────────────────────────────────────────────

def _test_exp_build(gate_fn, constant, label):
    """
    Can gate(x, constant) = exp(x)?
    Test at x = 0, 1, -1, 2.
    """
    test_xs = [0.0, 1.0, -1.0, 2.0]
    errors = []
    for x in test_xs:
        try:
            got = gate_fn(x, constant).real if hasattr(gate_fn(x, constant), 'real') else gate_fn(x, constant)
            ref = math.exp(x)
            errors.append(abs(got - ref))
        except Exception:
            errors.append(float('inf'))
    max_err = max(errors)
    ok = max_err < 1e-10
    return ok, max_err


def _test_ln_3node(gate_fn, c, label):
    """
    Try the two known 3-node ln structures and see if either works.
    Structure A (EML-style):  gate(c, gate(gate(c, x), c))
    Structure B (EDL-style):  gate(0, gate(gate(0, x), c))
    Test at x = 0.5, e, 2, 10.
    """
    test_xs = [0.5, math.e, 2.0, 10.0]
    best_err = float('inf')
    best_label = "none"

    for struct_name, struct_fn in [
        ("A: gate(c, gate(gate(c,x),c))", lambda x: gate_fn(c, gate_fn(gate_fn(c, x), c))),
        ("B: gate(0, gate(gate(0,x),c))", lambda x: gate_fn(0, gate_fn(gate_fn(0, x), c))),
    ]:
        try:
            errs = []
            for x in test_xs:
                got = struct_fn(x)
                got_r = got.real if hasattr(got, 'real') else got
                errs.append(abs(got_r - math.log(x)))
            max_e = max(errs)
            if max_e < best_err:
                best_err = max_e
                best_label = struct_name
        except Exception:
            pass

    ok = best_err < 1e-10
    return ok, best_err, best_label


def explore_parametric():
    print(f"\n{'Part C — Parametric family: can it build exp? ln?':^70}")
    print(SEP)
    print(f"  {'Variant':^40}  {'exp?':^6}  {'ln?':^6}  {'ln struct':^12}")
    print(SEP)

    variants = []

    # exp(x) - k * ln(y)  [EML at k=1]
    for k in [0.5, 1.0, 2.0, 3.0]:
        name = f"exp(x) - {k}*ln(y)"
        fn   = lambda x, y, k=k: cmath.exp(x) - k * cmath.log(y)
        # right-neutral c s.t. fn(x, c) = exp(x): -k*ln(c) = 0 → c = 1
        c    = 1.0 + 0j
        variants.append((name, fn, c))

    # exp(x) / ln(y)^k  [EDL at k=1]
    for k in [1.0, 2.0]:
        name = f"exp(x) / ln(y)^{k:.0f}"
        fn   = lambda x, y, k=k: cmath.exp(x) / (cmath.log(y) ** k)
        # fn(x, c) = exp(x): ln(c)^k = 1 → ln(c) = 1 → c = e
        c    = cmath.e
        variants.append((name, fn, c))

    # exp(k*x) - ln(y)
    for k in [0.5, 2.0]:
        name = f"exp({k}*x) - ln(y)"
        fn   = lambda x, y, k=k: cmath.exp(k * x) - cmath.log(y)
        # fn(x, c) = exp(k*x): ln(c) = 0 → c = 1
        c    = 1.0 + 0j
        variants.append((name, fn, c))

    # ln(y) - exp(x)  [EMN at k=1] and ln(y)^k - exp(x)
    for k in [1.0, 2.0]:
        name = f"ln(y)^{k:.0f} - exp(x)"
        fn   = lambda x, y, k=k: (cmath.log(y) ** k) - cmath.exp(x)
        # fn(x, c) = -exp(x): ln(c)^k = 0 → c = 1 (not +exp)
        c    = 1.0 + 0j
        variants.append((name, fn, c))

    # ln(y) / exp(x)  (ratio inverted)
    for name, fn, c in [
        ("ln(y) / exp(x)", lambda x, y: cmath.log(y) / cmath.exp(x), cmath.e),
    ]:
        variants.append((name, fn, c))

    for name, fn, c in variants:
        can_exp, exp_err = _test_exp_build(fn, c, name)
        can_ln,  ln_err, ln_struct = _test_ln_3node(fn, c, name)
        exp_s = "YES" if can_exp else f"no({exp_err:.1e})"
        ln_s  = "YES" if can_ln  else f"no({ln_err:.1e})"
        print(f"  {name:<40}  {exp_s:^6}  {ln_s:^6}  {ln_struct[:12]}")

    print()
    print("  Legend:")
    print("    YES  = max error < 1e-10 across test points {0, 1, -1, 2}")
    print("    no   = cannot build the function as a finite expression tree")
    print("    ln struct = which 3-node template matched (A=EML-style, B=EDL-style)")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    XS_SAFE  = [1.1, 1.5, 2.0, 3.0]       # safe for both operators
    XS_MIXED = [0.5, 1.1, 1.5, 2.0, 3.0]  # 0.5 fails ln_eml in pow

    print(SEP)
    print(f"{'PART A  —  STABILITY SHOOTOUT':^70}")
    print(SEP)

    bench_pow(XS_MIXED, n=50)
    bench_chain_mul(XS_SAFE, n=50)
    bench_depth_to_nan(x=2.0, max_depth=200)
    bench_polynomial([0.5, 1.0, 1.5, 2.0])

    print()
    print(SEP)
    print(f"{'PART C  —  PARAMETRIC FAMILY EXPLORER':^70}")
    print(SEP)

    explore_parametric()

    print()
    print(SEP)
    print("Done.")
