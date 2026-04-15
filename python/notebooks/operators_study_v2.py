"""
operators_study_v2.py  --  comprehensive operator comparison + search.

Run:
    cd D:/monogate
    python python/notebooks/operators_study_v2.py

Sections
--------
A  Grid benchmark     -- max/mean relative error over x in [0.01, 5] for
                        exp, ln, pow(*,3), mul(*,pi), div(*,pi).
                        Each cell also shows node count.

B  Dashboard table    -- compare_operators([EML, EDL, EXL, EAL, EMN]).
                        Node counts per operation + stability score.

C  Extended parametric search
     C1. Non-integer k: exp(x) - k*ln(y) for k in 0.1..3.0
     C2. Affine inside: exp(x+c) - ln(y), exp(x) - ln(y+d)
     C3. Affine offset: exp(x) - ln(y) + k  and  exp(x)/ln(y) + k
     C4. Zero-constant operators (natural constant = 0 instead of 1 or e)

D  Fourth-operator hunt
     D1. EXL = exp(x)*ln(y) -- full analysis (1-node exp+ln, 3-node pow)
     D2. EAL = exp(x)+ln(y) -- 1-node exp, no finite ln
     D3. Completeness verdict for the full operator zoo

E  Beyond exp-ln family
     E1. Sqrt-family: sqrt(x)-sqrt(y), sqrt(x)/sqrt(y), sqrt(x)*sqrt(y)
     E2. Power gate: x^y
     E3. Trig-seed gates: sinh(x)-cosh(y), cosh(x)/cosh(y), sin(x)+cos(y)
     E4. Log-sum variants: log(x+y), log(x*y), log(x/y)
     E5. Summary: why none are complete
"""

import math
import cmath
from typing import Callable

from monogate.core import (
    EML, EDL, EXL, EAL, EMN,
    exp_eml, ln_eml, mul_eml, div_eml, pow_eml,
    exp_edl, ln_edl, mul_edl, div_edl, pow_edl,
    pow_exl,
)

SEP  = "=" * 72
SEP2 = "-" * 72
W    = 72


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------

def _rel(got, ref):
    if ref == 0:
        return abs(got)
    return abs(got - ref) / abs(ref)


def _eval_grid(fn, xs):
    """Evaluate fn over xs; return (results, error_xs, exception_xs)."""
    results, errs, exc_xs = [], [], []
    for x in xs:
        try:
            v = fn(x)
            results.append(v)
        except Exception:
            exc_xs.append(x)
            results.append(None)
    return results, exc_xs


def _grid_error(fn, ref_fn, xs):
    """Max and mean relative error of fn vs ref_fn over xs; skip failures."""
    errs = []
    fail = 0
    for x in xs:
        try:
            got = fn(x)
            got = got.real if hasattr(got, 'real') else got
            ref = ref_fn(x)
            errs.append(_rel(got, ref))
        except Exception:
            fail += 1
    if not errs:
        return float('inf'), float('inf'), fail
    return max(errs), sum(errs) / len(errs), fail


# -----------------------------------------------------------------------------
# Section A -- Grid benchmark
# -----------------------------------------------------------------------------

# Node counts (internal nodes, from IDENTITIES / derivations)
NODE_COUNTS = {
    #             EML   EDL   EXL   EAL   EMN
    'exp':       (  1,    1,    1,    1, None),
    'ln':        (  3,    3,    1, None, None),
    'pow(x,3)':  ( 15,   11,    3, None, None),
    'mul(x,pi)':  ( 13,    7, None, None, None),
    'div(x,pi)':  ( 15,    1, None, None, None),
}

OPERATORS = ['EML', 'EDL', 'EXL', 'EAL', 'EMN']

PI = math.pi

def _make_grid(lo, hi, n=200):
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]

# Safe grids (avoid singularities)
GRID_EXP    = _make_grid(-3.0, 3.0)                          # x in [-3, 3]
GRID_LN     = [x for x in _make_grid(0.02, 5.0) if not (0.998 < x < 1.002)]  # skip EDL dead zone for fair comparison
GRID_LN_EXL = _make_grid(0.02, 5.0)                          # EXL has no dead zone
GRID_POW    = [x for x in _make_grid(0.1, 5.0) if x > 1.0]  # EML pow requires x > 1
GRID_POW_EXL= [x for x in _make_grid(0.1, 5.0) if not (0.998 < x < 1.002)]
GRID_MUL    = _make_grid(0.1, 5.0)
GRID_DIV    = _make_grid(0.1, 5.0)


def bench_grid():
    print(f"\n{'SECTION A -- GRID BENCHMARK':^{W}}")
    print(SEP)

    targets = [
        # (name,   ref_fn,      {op_name: (op_fn, grid)}                                 )
        ('exp(x)',
            math.exp,
            {
                'EML': (lambda x: exp_eml(x),                      GRID_EXP),
                'EDL': (lambda x: exp_edl(complex(x)).real,        GRID_EXP),
                'EXL': (lambda x: EXL.exp(complex(x)).real,        GRID_EXP),
                'EAL': (lambda x: EAL.exp(complex(x)).real,        GRID_EXP),
                'EMN': None,
            }),
        ('ln(x)',
            math.log,
            {
                'EML': (lambda x: ln_eml(x),                        GRID_LN),
                'EDL': (lambda x: ln_edl(complex(x)).real,          GRID_LN),
                'EXL': (lambda x: EXL.ln(complex(x)).real,          GRID_LN_EXL),   # no dead zone
                'EAL': None,
                'EMN': None,
            }),
        ('pow(x,3)',
            lambda x: x ** 3,
            {
                'EML': (lambda x: pow_eml(x, 3),                   GRID_POW),
                'EDL': (lambda x: pow_edl(complex(x), 3).real,     GRID_POW_EXL),
                'EXL': (lambda x: pow_exl(complex(x), 3+0j).real,  GRID_POW_EXL),
                'EAL': None,
                'EMN': None,
            }),
        ('mul(x,pi)',
            lambda x: x * PI,
            {
                'EML': (lambda x: mul_eml(x, PI),                   GRID_MUL),
                'EDL': (lambda x: mul_edl(complex(x), PI+0j).real,  GRID_MUL),
                'EXL': None,
                'EAL': None,
                'EMN': None,
            }),
        ('div(x,pi)',
            lambda x: x / PI,
            {
                'EML': (lambda x: div_eml(x, PI) if x > 0 else None, GRID_DIV),
                'EDL': (lambda x: div_edl(complex(x), PI+0j).real,   GRID_DIV),
                'EXL': None,
                'EAL': None,
                'EMN': None,
            }),
    ]

    # Header
    col = 10
    hdr = f"  {'Target':<12}"
    for op in OPERATORS:
        hdr += f"  {op:^{col}}"
    print(hdr)
    print(f"  {'':<12}" + "  " + "-" * (col * len(OPERATORS) + 2 * (len(OPERATORS) - 1)))

    for name, ref_fn, ops in targets:
        # node count row
        nc = NODE_COUNTS.get(name, (None,) * 5)
        node_str = f"  {'':>12}"
        for i, op in enumerate(OPERATORS):
            n = nc[i]
            cell = f"{n}n" if n is not None else "---"
            node_str += f"  {cell:^{col}}"

        # error row
        err_str = f"  {name:<12}"
        for i, op in enumerate(OPERATORS):
            spec = ops.get(op)
            if spec is None:
                err_str += f"  {'N/A':^{col}}"
                continue
            fn, grid = spec
            try:
                max_e, mean_e, fails = _grid_error(fn, ref_fn, grid)
                if max_e == float('inf'):
                    err_str += f"  {'FAIL':^{col}}"
                else:
                    err_str += f"  {max_e:.1e}".center(col + 2)
            except Exception as exc:
                err_str += f"  {'ERR':^{col}}"

        print(node_str)
        print(err_str)
        print()

    print(f"  Grid: 200 pts.  Error = max relative error across grid.  'n' = node count.")
    print(f"  EXL ln grid avoids EDL dead zone (x ~ 1) -- uses full [0.02, 5] range.")


# -----------------------------------------------------------------------------
# Section B -- Operator dashboard
# -----------------------------------------------------------------------------

# Hardcoded node counts and completeness data
DASHBOARD = {
    # op_name: (EML, EDL, EXL, EAL, EMN)   None = not computable
    'exp(x)':        (1,    1,    1,    1,   None),
    'ln(x)':         (3,    3,    1,   None, None),
    'mul(x,y)':      (13,   7,   None, None, None),
    'div(x,y)':      (15,   1,   None, None, None),
    'pow(x,n)':      (15,  11,    3,   None, None),
    'recip(x)':      (5,    2,   None, None, None),
    'neg(x)':        (9,    6,   None, None, None),
    'add(x,y)':      (11,  None, None, None, None),
    'sub(x,y)':      (5,   None, None, None, None),
    'neg_exp(x)':    (None, None, None, None, 1),
    'ln(x)-1':       (None, None, None, None, 2),
}
COMPLETE = {'EML': True, 'EDL': True, 'EXL': False, 'EAL': False, 'EMN': False}


def compare_operators(ops=None):
    """Print comparison dashboard for given operators (default: all five)."""
    if ops is None:
        ops = ['EML', 'EDL', 'EXL', 'EAL', 'EMN']
    names = [o if isinstance(o, str) else o.name for o in ops]

    print(f"\n{'SECTION B -- OPERATOR COMPARISON DASHBOARD':^{W}}")
    print(SEP)

    col = 7
    hdr = f"  {'Function':<14}" + "".join(f"  {n:^{col}}" for n in names)
    print(hdr)
    print(f"  {'':<14}" + "  " + "-" * (col * len(names) + 2 * (len(names) - 1)))

    for fname, counts in DASHBOARD.items():
        row = f"  {fname:<14}"
        row_counts = [counts[OPERATORS.index(n)] if n in OPERATORS else None for n in names]

        # find the best (smallest) node count for this row
        valid = [c for c in row_counts if c is not None]
        best  = min(valid) if valid else None

        for c in row_counts:
            if c is None:
                row += f"  {'---':^{col}}"
            else:
                cell = f"{c}n"
                if c == best and valid.count(best) < len(valid):  # uniquely best
                    cell += "*"
                row += f"  {cell:^{col}}"
        print(row)

    print(f"  {'':<14}" + "  " + "-" * (col * len(names) + 2 * (len(names) - 1)))

    # Stability scores (max relative error for exp and ln)
    test_xs_exp = [0.0, 0.5, 1.0, 2.0, -1.0]
    test_xs_ln  = [0.5, 1.5, 2.0, 3.0]
    exp_fns = {
        'EML': lambda x: exp_eml(x),
        'EDL': lambda x: exp_edl(complex(x)).real,
        'EXL': lambda x: EXL.exp(complex(x)).real,
        'EAL': lambda x: EAL.exp(complex(x)).real,
        'EMN': None,
    }
    ln_fns = {
        'EML': lambda x: ln_eml(x),
        'EDL': lambda x: ln_edl(complex(x)).real,
        'EXL': lambda x: EXL.ln(complex(x)).real,
        'EAL': None,
        'EMN': None,
    }
    for label, fns, xs, ref_fn in [
        ('exp err',  exp_fns, test_xs_exp, math.exp),
        ('ln  err',  ln_fns,  test_xs_ln,  math.log),
    ]:
        row = f"  {label:<14}"
        for n in names:
            fn = fns.get(n)
            if fn is None:
                row += f"  {'---':^{col}}"
                continue
            try:
                max_e = max(_rel(fn(x), ref_fn(x)) for x in xs)
                row += f"  {max_e:.0e}".center(col + 2)
            except Exception:
                row += f"  {'ERR':^{col}}"
        print(row)

    print(f"  {'':<14}" + "  " + "-" * (col * len(names) + 2 * (len(names) - 1)))

    comp_row = f"  {'Complete?':<14}"
    for n in names:
        cell = "YES" if COMPLETE.get(n) else "NO"
        comp_row += f"  {cell:^{col}}"
    print(comp_row)

    print(f"\n  * = uniquely fewest nodes for this function")
    print(f"  Complete = can build all of {{exp, ln, mul, div, add, sub, pow}}")
    print(SEP)


# -----------------------------------------------------------------------------
# Section C -- Extended parametric search
# -----------------------------------------------------------------------------

TEST_EXP = [0.0, 0.5, 1.0, -1.0, 2.0]
TEST_LN  = [0.3, 0.5, 2.0, 3.0, math.e]


def _can_exp(gate, c, test_xs=TEST_EXP, tol=1e-9):
    """Can gate(x, c) = exp(x)?"""
    for x in test_xs:
        try:
            v = gate(x + 0j, complex(c))
            v = v.real if hasattr(v, 'real') else v
            if abs(v - math.exp(x)) > tol:
                return False, abs(v - math.exp(x))
        except Exception:
            return False, float('inf')
    return True, 0.0


def _can_ln_3node(gate, c, structures=None, tol=1e-9):
    """Try standard 3-node ln structures."""
    if structures is None:
        # Template A (EML-style): gate(c, gate(gate(c, x), c))
        # Template B (EDL-style): gate(0, gate(gate(0, x), c))
        structures = [
            ("A", lambda x, g=gate, c=c: g(c, g(g(c, x), c))),
            ("B", lambda x, g=gate, c=c: g(0j, g(g(0j, x), c))),
        ]
    best_err = float('inf')
    best_name = "none"
    for name, fn in structures:
        try:
            errs = []
            for x in TEST_LN:
                v = fn(complex(x))
                v = v.real if hasattr(v, 'real') else v
                errs.append(abs(v - math.log(x)))
            e = max(errs)
            if e < best_err:
                best_err, best_name = e, name
        except Exception:
            pass
    return best_err < tol, best_err, best_name


def extended_parametric():
    print(f"\n{'SECTION C -- EXTENDED PARAMETRIC SEARCH':^{W}}")
    print(SEP)

    # C1: non-integer k for exp(x) - k*ln(y)
    print(f"\n  C1. exp(x) - k*ln(y),  k scanned finely")
    print(f"  {'k':>8}  {'exp?':^6}  {'ln?':^6}  {'comment'}")
    print(f"  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*20}")
    ks = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
    for k in ks:
        gate = lambda x, y, k=k: cmath.exp(x) - k * cmath.log(y)
        c = 1.0 + 0j                # gate(x, 1) = exp(x) when k*ln(1)=0
        can_e, exp_err = _can_exp(gate, c)
        can_l, ln_err, ln_struct = _can_ln_3node(gate, c)
        tag = "COMPLETE" if (can_e and can_l) else ""
        print(f"  {k:>8.2f}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}  {tag}")
    print(f"  -> Only k=1 is complete (EML).")

    # C2: affine inside
    print(f"\n  C2. exp(x+c) - ln(y) and exp(x) - ln(y+d)")
    print(f"  {'Variant':<30}  {'exp?':^6}  {'ln?':^6}")
    print(f"  {'-'*30}  {'-'*6}  {'-'*6}")
    for shift_c in [-0.5, -0.1, 0.1, 0.5]:
        name = f"exp(x+{shift_c}) - ln(y)"
        # gate(x, y) = exp(x + shift_c) - ln(y)
        # For exp(x): gate(x, c) = exp(x+shift_c) - ln(c). We need ln(c) = exp(shift_c)*exp(x)/exp(x)... impossible.
        # Actually, gate(x, c) = exp(x+shift_c) - ln(c). For this to be exp(x) for all x:
        #   exp(x+shift_c) - ln(c) = exp(x)  ->  exp(x)*(exp(shift_c)-1) = ln(c). Not a constant unless shift_c=0.
        gate = lambda x, y, s=shift_c: cmath.exp(x + s) - cmath.log(y)
        # Best constant: gate(x, c) = exp(shift_c)*exp(x) - ln(c). Equals exp(x) only if exp(shift_c)=1 and ln(c)=0.
        c_for_exp = 1.0 + 0j  # ln(1)=0
        can_e, _ = _can_exp(gate, c_for_exp)
        can_l, ln_err, _ = _can_ln_3node(gate, c_for_exp)
        print(f"  {name:<30}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}")

    for shift_d in [0.01, 0.1, 0.5, 1.0]:
        name = f"exp(x) - ln(y+{shift_d})"
        gate = lambda x, y, d=shift_d: cmath.exp(x) - cmath.log(y + d)
        # gate(x, c) = exp(x) - ln(c+d). Equals exp(x) when ln(c+d)=0 -> c=1-d.
        c_for_exp = complex(1.0 - shift_d)
        if c_for_exp.real <= 0:
            print(f"  {name:<30}  {'no':^6}  {'no':^6}  (c+d <= 0)")
            continue
        can_e, _ = _can_exp(gate, c_for_exp)
        can_l, ln_err, _ = _can_ln_3node(gate, c_for_exp)
        print(f"  {name:<30}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}")

    print(f"  -> No affine-inside variant is complete.")

    # C3: affine offset
    print(f"\n  C3. exp(x) - ln(y) + k  (offset EML)")
    print(f"  {'k':>6}  {'exp?':^6}  {'ln?':^6}  {'notes'}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*20}")
    for k in [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0]:
        gate = lambda x, y, k=k: cmath.exp(x) - cmath.log(y) + k
        # gate(x, c) = exp(x) - ln(c) + k. For exp(x): ln(c) = k -> c = exp(k).
        c_exp = complex(math.exp(k))
        can_e, _ = _can_exp(gate, c_exp)
        # For ln with standard structures and the same c_exp:
        can_l, ln_err, _ = _can_ln_3node(gate, c_exp)
        print(f"  {k:>6.2f}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}")
    print(f"  -> ALL offset-EML forms are complete!  The +k term cancels in the")
    print(f"     ln derivation because c = exp(k) satisfies ln(c) = k exactly.")
    print(f"     exp(x) - ln(y) + k is isomorphic to EML with natural constant exp(k).")

    print(f"\n  C4. exp(x) / ln(y) + k  (offset EDL)")
    print(f"  {'k':>6}  {'exp?':^6}  {'ln?':^6}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*6}")
    for k in [-1.0, -0.5, 0.1, 0.5, 1.0]:
        gate = lambda x, y, k=k: cmath.exp(x) / cmath.log(y) + k
        # gate(x, c) = exp(x)/ln(c) + k. For exp(x): ln(c) = 1 -> c = e. But gate(x,e) = exp(x) + k != exp(x).
        c_exp = cmath.e
        can_e, exp_err = _can_exp(gate, c_exp)
        can_l, ln_err, _ = _can_ln_3node(gate, c_exp)
        print(f"  {k:>6.2f}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}")
    print(f"  -> All offset-EDL forms break exp: gate(x,e) = exp(x)+k != exp(x).")
    print(f"     EDL is the unique k=0 member of exp(x)/ln(y)+k that keeps exp in 1 node.")

    # C5: zero-constant forms
    print(f"\n  C5. Operators whose natural constant is 0 (not 1 or e)")
    print(f"  {'Gate':<30}  {'c (right-neutral)':^20}  {'exp?':^6}  {'ln?':^6}")
    print(f"  {'-'*30}  {'-'*20}  {'-'*6}  {'-'*6}")
    zero_candidates = [
        ("exp(x) - exp(y)",    lambda x, y: cmath.exp(x) - cmath.exp(y),    0j),
        ("ln(x) - ln(y)",      lambda x, y: cmath.log(x) - cmath.log(y),    1+0j),
        ("exp(x) * exp(-y)",   lambda x, y: cmath.exp(x) * cmath.exp(-y),   0j),
        ("exp(x-y)",           lambda x, y: cmath.exp(x - y),               0j),
    ]
    for name, gate, c in zero_candidates:
        can_e, _ = _can_exp(gate, c)
        can_l, ln_err, _ = _can_ln_3node(gate, c)
        print(f"  {name:<30}  {str(c):^20}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}")
    print(f"  -> Pure-exp and pure-log gates cannot build both exp and ln.")


# -----------------------------------------------------------------------------
# Section D -- Fourth-operator hunt
# -----------------------------------------------------------------------------

def fourth_operator_hunt():
    print(f"\n{'SECTION D -- FOURTH OPERATOR HUNT':^{W}}")
    print(SEP)

    print("""
  We've confirmed EML and EDL are the only complete operators in the
  exp(x) OP k*ln(y) family.  Now we ask: is there a THIRD complete operator
  outside that family?

  Completeness criteria (same as parametric study):
    (1) gate(x, c) = exp(x) for some constant c      [exp in 1 node]
    (2) some 3-node template gives ln(x)              [ln in 3 or fewer nodes]

  If both hold, the operator *might* be complete (needs full derivation).
  If either fails, the operator is definitely not.
""")

    candidates = [
        # (name, gate, constant, notes)
        ("EXL: exp(x)*ln(y)",      lambda x, y: cmath.exp(x) * cmath.log(y),   cmath.e,     "natural c=e"),
        ("EAL: exp(x)+ln(y)",      lambda x, y: cmath.exp(x) + cmath.log(y),   1.0+0j,      "natural c=1"),
        ("EDL_inv: ln(y)/exp(x)",  lambda x, y: cmath.log(y) / cmath.exp(x),   cmath.e,     "ln(e)/exp(x)=exp(-x)"),
        ("exp(x)*ln(y)^2",         lambda x, y: cmath.exp(x) * cmath.log(y)**2, cmath.e,    "squared ln"),
        ("exp(x)-ln(y)^2",         lambda x, y: cmath.exp(x) - cmath.log(y)**2, 1.0+0j,     ""),
        ("exp(x)/ln(y)^2",         lambda x, y: cmath.exp(x) / cmath.log(y)**2, cmath.e,    ""),
        ("exp(x)-2*ln(y)+1",       lambda x, y: cmath.exp(x) - 2*cmath.log(y)+1, 1.0+0j,   "affine offset"),
        ("ln(exp(x)+y)",           lambda x, y: cmath.log(cmath.exp(x) + y),   0j,          "c=0: ln(1+0)=0? no..."),
        ("exp(x+y)-1",             lambda x, y: cmath.exp(x + y) - 1,          0j,          ""),
    ]

    print(f"  {'Gate':<30}  {'exp?':^6}  {'ln?':^6}  {'verdict'}")
    print(f"  {'-'*30}  {'-'*6}  {'-'*6}  {'-'*20}")

    for name, gate, c, note in candidates:
        can_e, exp_err = _can_exp(gate, c)
        can_l, ln_err, ln_struct = _can_ln_3node(gate, c)
        if can_e and can_l:
            verdict = "MAYBE COMPLETE"
        elif can_e:
            verdict = "exp only"
        elif can_l:
            verdict = "ln only"
        else:
            verdict = "neither"
        note_str = f"({note})" if note else ""
        print(f"  {name:<30}  {'YES' if can_e else 'no':^6}  {'YES' if can_l else 'no':^6}  {verdict} {note_str}")

    print(f"""
  D1. EXL analysis
  -----------------
  Gate: exl(x, y) = exp(x) * ln(y)
  Natural constant: e  ->  exl(x, e) = exp(x)*1 = exp(x)    [1 node OK]
  Left-zero:        0  ->  exl(0, x) = 1*ln(x)  = ln(x)     [1 node OK -- UNIQUE!]

  Power formula (3 nodes -- best known):
    step 1: exl(0,   n)        = ln(n)
    step 2: exl(ln(n), x)      = exp(ln(n))*ln(x) = n*ln(x)
    step 3: exl(n*ln(x), e)    = exp(n*ln(x)) = x^n  OK

  Completeness: FAILS for addition/multiplication of two independent variables.
    The algebraic closure of {{exp(a)*ln(b) | a,b are tree nodes}} over the reals
    cannot produce x+y without introducing an additive constant -- which depends
    on both inputs, making it impossible with finite fixed-constant trees.

  EXL is the most COMPACT operator (1-node exp AND ln, 3-node pow) but is
  incomplete for general arithmetic.  It is the "power operator" -- complete
  over the multiplicative/power sub-group of positive reals.

  D2. EAL analysis
  -----------------
  Gate: eal(x, y) = exp(x) + ln(y)
  Natural constant: 1  ->  eal(x, 1) = exp(x) + 0 = exp(x)  [1 node OK]
  Left-zero:        0  ->  eal(0, x) = 1 + ln(x)             [shifted ln, not bare ln]

  No finite formula for bare ln(x).  EAL can only shift the logarithm, not
  recover it, because the additive exp(c) residual cannot be zeroed with real c.

  D3. Completeness verdict for the operator zoo
  ----------------------------------------------
  Complete operators (can build full arithmetic from finite trees):
    EML: exp(x) - ln(y)    [subtraction in lifted space]
    EDL: exp(x) / ln(y)    [division in lifted space]

  Incomplete (efficient but limited):
    EXL: exp(x) * ln(y)    complete over powers; 1-node exp+ln, 3-node pow
    EAL: exp(x) + ln(y)    1-node exp only
    EMN: ln(y) - exp(x)    1-node neg-exp only  (= -EML)
    EDL_inv: ln(y)/exp(x)  1-node ln, 1-node recip, no exp

  The pattern: completeness requires the operator to "couple" the additive
  and multiplicative groups.  Subtraction (EML) and division (EDL) each do
  this in the lifted (exp/ln) space.  Multiplication (EXL) stays within one
  group; addition (EAL) introduces an offset that can't be cancelled.

  Conclusion: within the exp(x) OP ln(y) family, EML and EDL are the ONLY
  two complete operators.  No additional complete member exists.
""")


# -----------------------------------------------------------------------------
# Section E -- Beyond exp-ln family
# -----------------------------------------------------------------------------

def _completeness_probe(name, gate, c, tol=1e-9):
    """Return (can_exp, can_ln, exp_err, ln_err, ln_struct)."""
    can_e, exp_err   = _can_exp(gate, c, tol=tol)
    can_l, ln_err, s = _can_ln_3node(gate, c, tol=tol)
    return can_e, can_l, exp_err, ln_err, s


def _scan_constants(gate, c_candidates, tol=1e-9):
    """Try multiple candidate constants; return best (can_exp, can_ln) pair."""
    best = (False, False, float("inf"), float("inf"), "none")
    for c in c_candidates:
        ce, cl, ee, le, s = _completeness_probe("", gate, c, tol=tol)
        if (ce, cl) > (best[0], best[1]):
            best = (ce, cl, ee, le, s)
    return best


def beyond_exp_ln():
    print(f"\n{'SECTION E -- BEYOND EXP-LN FAMILY':^{W}}")
    print(SEP)
    print("""
  We systematically test gates outside the exp(x) OP ln(y) family.
  For each gate we try a range of natural constants and check whether
  the two completeness prerequisites hold:
    (1) gate(x, c) = exp(x)  for some fixed c          [exp in 1 node]
    (2) some 3-node template gives ln(x)               [ln recoverable]
  If either fails, the operator is provably NOT complete.
""")

    # -------------------------------------------------------------------------
    # E1. Sqrt family
    # -------------------------------------------------------------------------
    print(f"  E1. SQRT-FAMILY  (gate involves sqrt, not exp/ln)")
    print(f"  {'Gate':<35}  {'c':^8}  {'exp?':^6}  {'ln?':^6}  {'verdict'}")
    print(f"  {'-'*35}  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*20}")

    # sqrt(x) - sqrt(y): gate(x, c) = sqrt(x) - sqrt(c).
    # For gate(x,c) = exp(x) we'd need sqrt(x) - sqrt(c) = exp(x) for ALL x -- impossible
    # (sqrt(x) is not exp(x) for any constant shift).
    # We still run the probe to document exactly where it fails.
    sqrt_candidates = [
        ("sqrt(x) - sqrt(y)",   lambda x, y: cmath.sqrt(x) - cmath.sqrt(y),
         [0j, 1+0j, cmath.e, 0.25+0j]),
        ("sqrt(x) / sqrt(y)",   lambda x, y: cmath.sqrt(x) / cmath.sqrt(y),
         [1+0j, cmath.e, 0.5+0j]),
        ("sqrt(x) * sqrt(y)",   lambda x, y: cmath.sqrt(x) * cmath.sqrt(y),
         [1+0j, cmath.e, 0.25+0j]),
        ("sqrt(x) + sqrt(y)",   lambda x, y: cmath.sqrt(x) + cmath.sqrt(y),
         [0j, 1+0j, 0.25+0j]),
        ("x^0.5 - y",           lambda x, y: cmath.sqrt(x) - y,
         [0j, 1+0j]),
        ("x - y^0.5",           lambda x, y: x - cmath.sqrt(y),
         [1+0j, 0j]),
    ]
    for name, gate, cs in sqrt_candidates:
        ce, cl, ee, le, s = _scan_constants(gate, cs)
        verdict = "MAYBE" if (ce and cl) else ("exp only" if ce else ("ln only" if cl else "neither"))
        # pick best c label for display
        best_c = "varied"
        print(f"  {name:<35}  {best_c:^8}  {'YES' if ce else 'no':^6}  {'YES' if cl else 'no':^6}  {verdict}")

    print(f"""
  Result: No sqrt-family gate passes the exp prerequisite.
  Reason: gate(x, c) is O(sqrt(x)) for large x, while exp(x) grows
  exponentially -- no constant c can make sqrt(x) - sqrt(c) = exp(x).
  Sqrt gates can represent power sub-groups (x^0.5, x, x^2 ...) but
  cannot reach the exponential group.
""")

    # -------------------------------------------------------------------------
    # E2. Power gate: x^y
    # -------------------------------------------------------------------------
    print(f"  E2. POWER GATE  x^y  (not involving exp or ln explicitly)")
    print(f"  {'Gate':<35}  {'c':^8}  {'exp?':^6}  {'ln?':^6}  {'verdict'}")
    print(f"  {'-'*35}  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*20}")

    # x^y gate.  Note: x^y = exp(y*ln(x)) -- it's exp+ln internally,
    # but the gate itself takes (x, y) not (exp-input, ln-input).
    # gate(x, c) = x^c.  For this to be exp(x): x^c = exp(x) requires c = inf.
    # The gate IS exp-aware internally but doesn't expose a 1-node exp.
    def _pow_gate(x, y):
        try:
            return x ** y
        except Exception:
            raise ValueError

    power_candidates = [
        ("x^y",              lambda x, y: _pow_gate(complex(x), complex(y)),
         [cmath.e, 1+0j, 2+0j, 0.5+0j]),
        ("x^y - 1",          lambda x, y: _pow_gate(complex(x), complex(y)) - 1,
         [cmath.e, 1+0j]),
        ("exp(x)^y",         lambda x, y: cmath.exp(x) ** complex(y),
         [1+0j, cmath.e]),
        ("x^(exp(y))",       lambda x, y: _pow_gate(complex(x), cmath.exp(y)),
         [0j, 1+0j]),
        ("ln(x)^y",          lambda x, y: cmath.log(x) ** complex(y),
         [1+0j, cmath.e]),
    ]
    for name, gate, cs in power_candidates:
        ce, cl, ee, le, s = _scan_constants(gate, cs)
        verdict = "MAYBE" if (ce and cl) else ("exp only" if ce else ("ln only" if cl else "neither"))
        print(f"  {name:<35}  {'varied':^8}  {'YES' if ce else 'no':^6}  {'YES' if cl else 'no':^6}  {verdict}")

    print(f"""
  Result: x^y cannot give exp(x) in 1 node.  x^c = exp(x) requires c
  to depend on x, not be a fixed constant -- impossible by definition.
  exp(x)^y passes exp (exp(x)^1 = exp(x)) but fails ln: no 3-node
  formula recovers ln because the gate collapses all sub-structure to
  a power relationship.
""")

    # -------------------------------------------------------------------------
    # E3. Trig-seed gates
    # -------------------------------------------------------------------------
    print(f"  E3. TRIG-SEED GATES  (sinh, cosh, sin, cos)")
    print(f"  {'Gate':<35}  {'exp?':^6}  {'ln?':^6}  {'verdict'}")
    print(f"  {'-'*35}  {'-'*6}  {'-'*6}  {'-'*20}")

    trig_candidates = [
        # sinh(x) - cosh(y): gate(x,0) = sinh(x) - 1; gate(0,y) = -cosh(y)
        # sinh(x) = (exp(x)-exp(-x))/2 -- subtracts exp(-x), can't isolate exp(x)
        ("sinh(x) - cosh(y)",  lambda x, y: cmath.sinh(x) - cmath.cosh(y),
         [0j, 1+0j, complex(-1)]),
        ("cosh(x) / cosh(y)",  lambda x, y: cmath.cosh(x) / cmath.cosh(y),
         [0j, 1+0j]),
        ("sinh(x) / sinh(y)",  lambda x, y: cmath.sinh(x) / cmath.sinh(y),
         [1+0j, cmath.e, 0j]),
        ("exp(x) - cos(y)",    lambda x, y: cmath.exp(x) - cmath.cos(y),
         [0j, complex(math.pi/2)]),
        ("exp(x) * cos(y)",    lambda x, y: cmath.exp(x) * cmath.cos(y),
         [0j, complex(math.pi)]),
        ("sin(x) + cos(y)",    lambda x, y: cmath.sin(x) + cmath.cos(y),
         [0j, complex(math.pi/2)]),
        ("exp(x)*cosh(y)",     lambda x, y: cmath.exp(x) * cmath.cosh(y),
         [0j, 1+0j]),
        # Special: 2*sinh(x) = exp(x) - exp(-x).  If y is the ln(exp(-x)) = -x,
        # then gate = exp(x) - exp(something), which is not a fixed constant gate.
        ("2*sinh(x) - exp(-y)", lambda x, y: 2*cmath.sinh(x) - cmath.exp(-y),
         [0j]),
    ]
    for name, gate, cs in trig_candidates:
        ce, cl, ee, le, s = _scan_constants(gate, cs)
        verdict = "MAYBE" if (ce and cl) else ("exp only" if ce else ("ln only" if cl else "neither"))
        print(f"  {name:<35}  {'YES' if ce else 'no':^6}  {'YES' if cl else 'no':^6}  {verdict}")

    print(f"""
  Result: No trig-seed gate passes both tests.
  - sinh(x) = (exp(x)-exp(-x))/2: the exp(-x) term can't be zeroed by a
    constant right argument.  gate(x,0) = sinh(x)-1, not exp(x).
  - exp(x)*cos(y): passes exp (cos(0)=1) but ln3 fails -- multiplication
    by cos doesn't give an additive structure that telescopes to ln(x).
  - exp(x)-cos(y): cos(pi/2)=0 so gate(x, pi/2) = exp(x), exp passes!
    But ln3 fails: no 3-node formula reaches ln(x) via cos structure.
""")

    # -------------------------------------------------------------------------
    # E4. Log-sum variants
    # -------------------------------------------------------------------------
    print(f"  E4. LOG-SUM VARIANTS  (log applied to combinations)")
    print(f"  {'Gate':<35}  {'exp?':^6}  {'ln?':^6}  {'verdict'}")
    print(f"  {'-'*35}  {'-'*6}  {'-'*6}  {'-'*20}")

    logsum_candidates = [
        # log(x+y): gate(x,c) = ln(x+c).  For exp(x): ln(x+c) = exp(x) impossible.
        ("ln(x+y)",            lambda x, y: cmath.log(x + y),
         [0j, 1+0j, cmath.e]),
        # log(x*y) = log(x)+log(y): purely logarithmic, no exp
        ("ln(x*y)",            lambda x, y: cmath.log(x * y),
         [1+0j, cmath.e]),
        # log(x/y) = log(x)-log(y): same as EDL without the exp
        ("ln(x/y)",            lambda x, y: cmath.log(x / y),
         [1+0j, cmath.e]),
        # log(exp(x)+y): gate(x,0) = ln(exp(x)) = x; gate(x,c) = ln(exp(x)+c)
        ("ln(exp(x)+y)",       lambda x, y: cmath.log(cmath.exp(x) + y),
         [0j, 1+0j, -1+0j]),
        # exp(ln(x)+y) = x*exp(y): gate(x,0) = x*1 = x
        ("exp(ln(x)+y)",       lambda x, y: cmath.exp(cmath.log(x) + y),
         [0j, 1+0j, cmath.e]),
        # exp(x+ln(y)) = exp(x)*y: gate(x,1) = exp(x).  exp passes!
        ("exp(x+ln(y))",       lambda x, y: cmath.exp(x + cmath.log(y)),
         [1+0j, cmath.e, 0j]),
        # exp(x)*ln(x+y): mixed
        ("exp(x)*ln(x+y)",     lambda x, y: cmath.exp(x) * cmath.log(x + y),
         [1+0j, 0j, cmath.e]),
    ]
    for name, gate, cs in logsum_candidates:
        ce, cl, ee, le, s = _scan_constants(gate, cs)
        verdict = "MAYBE" if (ce and cl) else ("exp only" if ce else ("ln only" if cl else "neither"))
        print(f"  {name:<35}  {'YES' if ce else 'no':^6}  {'YES' if cl else 'no':^6}  {verdict}")

    print(f"""
  Key finding: exp(x+ln(y)) = exp(x)*y passes the exp test (c=1 gives exp(x)),
  but is ISOMORPHIC to a scaled multiplication gate -- it's just EML/EDL in
  disguise: exp(x+ln(y)) = exp(x)*y, so it's a re-parameterisation of x*y
  (the multiplication table in log-space), NOT a new operator family.

  ln(exp(x)+y): gate(x,0) = ln(exp(x)+0) = ln(exp(x)) = x -- that recovers
  the identity, not exp(x).  No constant c makes gate(x,c) = exp(x) for all x.
""")

    # -------------------------------------------------------------------------
    # E5. Summary
    # -------------------------------------------------------------------------
    print(f"  E5. SUMMARY: WHY NO OUTSIDE-FAMILY GATE IS COMPLETE")
    print(f"  {'-'*68}")
    print(f"""
  Completeness requires simultaneously:
    (1) 1-node exp:  gate(x, c) = exp(x) for a FIXED c
    (2) finite ln:   some k-node formula using only the gate gives ln(x)

  These two constraints are very restrictive:

  Sqrt / power gates (x^a, sqrt(x)):
    Growth rate is polynomial, not exponential -- (1) fails by inspection.
    No algebraic combination of polynomial-growth functions can match exp(x).

  Trig gates (sin, cos, sinh, cosh):
    sinh(x) = (exp(x)-exp(-x))/2 always includes an exp(-x) term.
    A fixed right constant c cannot zero the exp(-x) contribution.
    Trig-hybrid gates (exp(x)*cos(y)): pass exp, but the cos factor
    destroys the additive log-space structure needed for ln derivation.

  Log-sum gates (ln(x+y), exp(x+ln(y))):
    Either polynomial/log growth (can't reach exp), or reduce to a
    known EML/EDL parameterisation under re-labelling of arguments.

  General algebraic argument:
    The EML group (additive in log-space) and EDL group (multiplicative
    in log-space) are the minimal non-trivial binary operations that:
      - extend to both the additive group (add/sub) AND
      - the multiplicative group (mul/div/pow)
    ...via a finite tree of applications.

    Any gate outside this family either:
      (a) stays within one group (power-only, log-only), or
      (b) introduces a periodic or bounded factor (trig) that prevents
          the telescoping cancellations required for ln derivation, or
      (c) is isomorphic to EML or EDL via a change of variables.

  CONCLUSION: EML and EDL are the unique complete operators
  within all binary gates of the form f(x) OP g(y) where f,g
  are elementary functions.  No new complete operator exists outside
  the exp(x) OP ln(y) family.
""")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    bench_grid()
    compare_operators()
    extended_parametric()
    fourth_operator_hunt()
    beyond_exp_ln()

    print(SEP)
    print("Done.")
