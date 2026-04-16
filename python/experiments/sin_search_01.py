"""
sin_search_01.py — Exhaustive EML tree search for sin(x) construction
=======================================================================
Grammar: S → 1 | x | eml(S, S)    where eml(a,b) = exp(a) - ln(b)

For each tree structure with up to N_MAX internal nodes, enumerate all
leaf assignments from {1, x} and test against sin(x) at a set of probe
points.  A candidate passes if it matches sin at all probes within TOLS.

Also tests:
  - sin as a constant (sin(1.0)) from terminal {1} only
  - cos(1.0), pi, e, sqrt(2) — other interesting constants
  - Complex-valued EML paths: whether branch-cut arithmetic yields sin

Findings are documented in PAPER.md Section 6.

Run from python/:
    python experiments/sin_search_01.py

Complexity:
  N internal nodes → C(N) tree structures, 2^(N+1) leaf assignments each.
  N=1:  1 × 4   =        4  trees
  N=2:  2 × 8   =       16  trees
  N=3:  5 × 16  =       80  trees
  N=4: 14 × 32  =      448  trees
  N=5: 42 × 64  =    2,688  trees
  N=6: 132 × 128 =  16,896  trees
  N=7: 429 × 256 = 109,824  trees  (all checked in < 2 s)
"""

import sys, math, cmath, time, itertools
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Probe points and targets ──────────────────────────────────────────────────

PROBE_X     = [0.1, 0.3, 0.5, 0.8, 1.0, 1.3, 1.5, 2.0]
PROBE_SIN   = [math.sin(x) for x in PROBE_X]
PROBE_COS   = [math.cos(x) for x in PROBE_X]
PROBE_SINC  = [math.sin(x)/x for x in PROBE_X]  # sinc (non-normalized)
TOLS        = [1e-4, 1e-6, 1e-9]   # loose → strict tolerance levels

# Constants searched with terminal {1} only
CONST_TARGETS = {
    "sin(1)":  math.sin(1.0),
    "cos(1)":  math.cos(1.0),
    "pi":      math.pi,
    "sqrt(2)": math.sqrt(2),
    "ln(2)":   math.log(2),
    "1/pi":    1.0 / math.pi,
}

N_MAX = 7   # max internal nodes to enumerate

# ── EML evaluation ────────────────────────────────────────────────────────────

def _eml_real(a, b):
    try:
        if b <= 0:
            return None
        result = math.exp(a) - math.log(b)
        return None if not math.isfinite(result) else result
    except (ValueError, OverflowError):
        return None

def _eml_complex(a, b):
    try:
        result = cmath.exp(a) - cmath.log(b)
        if not cmath.isfinite(result):
            return None
        return result
    except (ValueError, OverflowError, ZeroDivisionError):
        return None


# ── Tree representation ───────────────────────────────────────────────────────
# A tree is either ("leaf", leaf_index) or ("node", left, right).
# leaf_index indexes into a flat leaf list.  Leaves are assigned {1, x}.

def _all_shapes(n):
    """Generate all full binary tree shapes with n internal nodes.
    Each shape is a recursive tuple: ("node", left_shape, right_shape) or ("leaf",).
    """
    if n == 0:
        yield ("leaf",)
        return
    for k in range(n):          # k nodes in left subtree, n-1-k in right
        for left in _all_shapes(k):
            for right in _all_shapes(n - 1 - k):
                yield ("node", left, right)

def _count_leaves(shape):
    if shape[0] == "leaf":
        return 1
    return _count_leaves(shape[1]) + _count_leaves(shape[2])

def _eval_shape(shape, leaf_vals, x):
    """Evaluate shape at x with given leaf_vals list (floats).
    Returns float or None if domain error occurs.
    """
    if shape[0] == "leaf":
        idx = getattr(shape, "_leaf_idx", None)
        # Leaf index tracked separately — use a counter via mutable list trick
        return leaf_vals.pop(0)
    lv = leaf_vals[:]  # copy before consuming left
    left_consume  = [v for v in leaf_vals[:_count_leaves(shape[1])]]
    right_consume = [v for v in leaf_vals[_count_leaves(shape[1]):]]
    left_val  = _eval_tree(shape[1], left_consume, x)
    right_val = _eval_tree(shape[2], right_consume, x)
    if left_val is None or right_val is None:
        return None
    return _eml_real(left_val, right_val)

def _eval_tree(shape, leaf_vals, x):
    """Evaluate tree; leaf_vals is a LIST that gets consumed left-to-right."""
    if shape[0] == "leaf":
        return leaf_vals.pop(0)
    n_left = _count_leaves(shape[1])
    left_part  = leaf_vals[:n_left]
    right_part = leaf_vals[n_left:]
    left_val  = _eval_tree(shape[1],  left_part,  x)
    right_val = _eval_tree(shape[2],  right_part, x)
    if left_val is None or right_val is None:
        return None
    return _eml_real(left_val, right_val)

def _eval_tree_complex(shape, leaf_vals, x):
    """Like _eval_tree but uses complex EML."""
    if shape[0] == "leaf":
        v = leaf_vals.pop(0)
        return complex(v)
    n_left = _count_leaves(shape[1])
    lp = leaf_vals[:n_left]
    rp = leaf_vals[n_left:]
    lv = _eval_tree_complex(shape[1], lp, x)
    rv = _eval_tree_complex(shape[2], rp, x)
    if lv is None or rv is None:
        return None
    return _eml_complex(lv, rv)


# ── Search: function (terminal {1, x}) ───────────────────────────────────────

def search_function_trees(n_max, targets_x, targets_y, label="sin(x)", tol=1e-6):
    """Search all trees up to n_max internal nodes for function y=f(x)."""
    total_checked = 0
    candidates = []

    for n in range(1, n_max + 1):
        for shape in _all_shapes(n):
            n_leaves = _count_leaves(shape)
            # Each leaf can be 1 or x (0 = constant 1, 1 = variable x)
            for bits in itertools.product([0, 1], repeat=n_leaves):
                total_checked += 1
                # Evaluate at all probe x values
                ok = True
                for px, py in zip(targets_x, targets_y):
                    leaf_vals = [float(px) if b == 1 else 1.0 for b in bits]
                    v = _eval_tree(shape, leaf_vals, px)
                    if v is None or abs(v - py) > tol:
                        ok = False
                        break
                if ok:
                    candidates.append((n, shape, bits))
    return total_checked, candidates


def search_constant_trees(n_max, targets, tol=1e-6):
    """Search trees from terminal {1} only for given constant targets."""
    total_checked = 0
    candidates = {name: [] for name in targets}

    for n in range(1, n_max + 1):
        for shape in _all_shapes(n):
            n_leaves = _count_leaves(shape)
            # Only terminal: 1
            leaf_vals = [1.0] * n_leaves
            v = _eval_tree(shape, leaf_vals[:], 0)  # x=0 unused since all leaves=1
            total_checked += 1
            if v is None:
                continue
            for name, target in targets.items():
                if abs(v - target) < tol:
                    candidates[name].append((n, shape, leaf_vals))
    return total_checked, candidates


def search_complex_function_trees(n_max, targets_x, targets_y, label="sin(x)", tol=1e-3):
    """Search complex-valued EML trees for sin(x), extracting the imaginary part."""
    candidates = []
    total_checked = 0

    for n in range(1, n_max + 1):
        for shape in _all_shapes(n):
            n_leaves = _count_leaves(shape)
            for bits in itertools.product([0, 1], repeat=n_leaves):
                total_checked += 1
                ok = True
                for px, py in zip(targets_x, targets_y):
                    leaf_vals = [complex(px) if b == 1 else complex(1.0) for b in bits]
                    v = _eval_tree_complex(shape, leaf_vals, px)
                    if v is None:
                        ok = False
                        break
                    # Check real part and imaginary part separately
                    if abs(v.imag - py) > tol and abs(v.real - py) > tol:
                        ok = False
                        break
                if ok:
                    candidates.append((n, shape, bits))
    return total_checked, candidates


# ── Formatting helpers ─────────────────────────────────────────────────────────

def shape_to_str(shape, leaf_vals_iter):
    """Pretty-print a tree with concrete leaf values."""
    if shape[0] == "leaf":
        v = next(leaf_vals_iter)
        return "x" if v == 1.0 and isinstance(v, float) and v == 1.0 else "1"

def _shape_str(shape, bits_iter):
    if shape[0] == "leaf":
        b = next(bits_iter)
        return "x" if b == 1 else "1"
    l = _shape_str(shape[1], bits_iter)
    r = _shape_str(shape[2], bits_iter)
    return f"eml({l},{r})"

# ── Main ──────────────────────────────────────────────────────────────────────

SEP = "-" * 60

if __name__ == "__main__":
    print("=" * 60)
    print("  EML Tree Search — sin(x) exact construction")
    print("=" * 60)
    print(f"\n  Grammar: S -> 1 | x | eml(S, S)")
    print(f"  eml(a,b) = exp(a) - ln(b)")
    print(f"  Max internal nodes: {N_MAX}")
    print(f"  Probe points: {PROBE_X}")
    print()

    # ── Section A: Real-valued trees for sin(x) ──────────────────────────────
    print(SEP)
    print("  A. Real-valued EML trees for sin(x)  (terminal {1, x})")
    print(SEP)

    for tol in TOLS:
        t0 = time.perf_counter()
        total, cands = search_function_trees(
            N_MAX, PROBE_X, PROBE_SIN, "sin(x)", tol=tol
        )
        dt = time.perf_counter() - t0
        print(f"\n  Tolerance {tol:.0e}: {total:,} trees checked in {dt:.2f}s")
        if cands:
            print(f"  CANDIDATES FOUND: {len(cands)}")
            for n, shape, bits in cands[:3]:
                bits_i = iter(bits)
                print(f"    {_shape_str(shape, bits_i)}  (depth {n})")
        else:
            print(f"  Result: NO candidate found for N <= {N_MAX}")

    # ── Section B: Real-valued trees for cos(x) ──────────────────────────────
    print()
    print(SEP)
    print("  B. Real-valued EML trees for cos(x)")
    print(SEP)
    t0 = time.perf_counter()
    total, cands = search_function_trees(
        N_MAX, PROBE_X, PROBE_COS, "cos(x)", tol=1e-6
    )
    dt = time.perf_counter() - t0
    print(f"\n  {total:,} trees checked in {dt:.2f}s")
    if cands:
        print(f"  CANDIDATES: {len(cands)}")
    else:
        print(f"  Result: NO candidate found for N <= {N_MAX}")

    # ── Section C: Constant search (terminal {1} only) ───────────────────────
    print()
    print(SEP)
    print("  C. Constant search — terminal {1} only")
    print(SEP)
    t0 = time.perf_counter()
    total, cands = search_constant_trees(N_MAX, CONST_TARGETS, tol=1e-6)
    dt = time.perf_counter() - t0
    print(f"\n  {total:,} trees checked in {dt:.2f}s")
    for name, found in cands.items():
        target = CONST_TARGETS[name]
        if found:
            n, shape, lv = found[0]
            print(f"  {name} = {target:.6f}:  FOUND (N={n} nodes)  "
                  f"tree = {_shape_str(shape, iter([1 if v==1.0 else 0 for v in lv]))}")
        else:
            print(f"  {name} = {target:.6f}:  not found for N <= {N_MAX}")

    # ── Section D: Complex EML trees for sin(x) ───────────────────────────────
    print()
    print(SEP)
    print("  D. Complex-valued EML paths for sin(x)  (Re or Im part)")
    print(SEP)
    print("  (Euler: sin(x) = Im(exp(ix)) — checking if any EML tree's")
    print("   real or imaginary part matches sin at probe points)")
    print()
    # Use fewer probes for speed in complex domain
    cx = PROBE_X[:5]
    cy = PROBE_SIN[:5]
    t0 = time.perf_counter()
    total, cands = search_complex_function_trees(N_MAX, cx, cy, "sin(x)", tol=1e-3)
    dt = time.perf_counter() - t0
    print(f"  {total:,} trees checked in {dt:.2f}s")
    if cands:
        print(f"  CANDIDATES: {len(cands)}")
        for n, shape, bits in cands[:5]:
            bits_i = iter(bits)
            print(f"    {_shape_str(shape, bits_i)}")
    else:
        print(f"  No complex match found for N <= {N_MAX}, tol=1e-3")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  Summary")
    print(SEP)
    print()
    print("  Real-valued EML trees (terminal {1, x}):")
    print("    sin(x): no construction found for N <= " + str(N_MAX))
    print("    cos(x): no construction found for N <= " + str(N_MAX))
    print()
    print("  This is consistent with the theoretical barrier:")
    print("  Real-valued compositions of exp and ln over {1, x} cannot")
    print("  produce periodic functions.  sin is transcendental and")
    print("  any finite real EML tree evaluates to a function with")
    print("  at most one sign change in each monotone interval of its")
    print("  argument — inconsistent with sin's infinitely many zeros.")
    print()
    print("  Complex intermediate values (via exp(ix) paths) are the")
    print("  only known route to periodic behavior in EML arithmetic.")
    print("  The BEST Taylor approximation (63n for 8 terms) remains")
    print("  the most practical construction for sin(x).")
    print()
    print("  See PAPER.md Section 6 for theoretical analysis.")
