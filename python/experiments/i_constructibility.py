"""
S61 — i-Constructibility: Setup and Attack

Question: can any finite EML tree with terminal {1} and strict principal-branch ln
evaluate to i = sqrt(-1)?

Naive argument:
  exp(real) is real and positive.
  ln(positive real) is real.
  real - real is real.
  Therefore all nodes in a {1}-seeded tree are real → i unreachable.

The loophole:
  eml(x, y) = exp(x) - ln(y)
  If y ≤ 0, principal-branch ln(y) = ln|y| + iπ  (complex).
  So if any node routes a non-positive value into the y-slot of an eml,
  complex values enter the tree.

This script:
  1. Enumerates ALL full binary EML trees with N internal nodes, N=1..7.
  2. For each tree, evaluates at the terminal assignment (every leaf = 1).
  3. Tracks sign/domain of every intermediate node.
  4. Records whether any intermediate y-argument is ≤ 0.
  5. If a tree produces a negative y-argument: traces whether i is reachable
     by choosing leaves optimally (still from {1}, but different subtree shapes).

DELIVERABLE: either proof that i is unreachable, or a witness tree.
"""

import itertools
import cmath
import math
import json
from pathlib import Path

# ── EML evaluation (principal-branch, complex-aware) ─────────────────────────

_EXP_CLAMP = 700.0  # exp(x) overflows f64 for x > ~709

def eml(x, y):
    """eml(x, y) = exp(x) - ln(y), principal branch ln."""
    try:
        if isinstance(x, complex) or isinstance(y, complex):
            if y == 0:
                return None
            return cmath.exp(x) - cmath.log(y)
        # real path — clamp to avoid overflow
        if isinstance(x, float) and (x > _EXP_CLAMP or x < -_EXP_CLAMP):
            return None  # overflow / underflow → treat as domain error
        if y <= 0:
            if y == 0:
                return None
            return math.exp(x) - cmath.log(y)  # returns complex
        return math.exp(x) - math.log(y)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


# ── Tree representation ───────────────────────────────────────────────────────
# A tree is either:
#   ('leaf',)          — a terminal node (evaluates to 1)
#   ('node', L, R)     — internal node: eml(eval(L), eval(R))

def all_trees(n_internal):
    """Generate all full binary trees with exactly n_internal internal nodes."""
    if n_internal == 0:
        yield ('leaf',)
        return
    for left_size in range(n_internal):
        right_size = n_internal - 1 - left_size
        for left in all_trees(left_size):
            for right in all_trees(right_size):
                yield ('node', left, right)


def eval_tree(tree, trace=None):
    """
    Evaluate tree with all leaves = 1.
    If trace is a list, appends (node_type, x_val, y_val, result) for each internal node.
    Returns the root value, or None on domain error.
    """
    if tree[0] == 'leaf':
        return 1.0
    _, left, right = tree
    lv = eval_tree(left, trace)
    rv = eval_tree(right, trace)
    if lv is None or rv is None:
        return None
    result = eml(lv, rv)
    if trace is not None:
        trace.append({
            'x': lv if not isinstance(lv, complex) else (lv.real, lv.imag),
            'y': rv if not isinstance(rv, complex) else (rv.real, rv.imag),
            'y_is_nonpositive': (isinstance(rv, (int, float)) and rv <= 0) or
                                 (isinstance(rv, complex) and rv.imag == 0 and rv.real <= 0),
            'result': result if not isinstance(result, complex) else (result.real, result.imag),
            'result_is_complex': isinstance(result, complex) and result.imag != 0,
        })
    return result


def is_i(val, tol=1e-9):
    """Check if val ≈ i = sqrt(-1)."""
    if not isinstance(val, complex):
        return False
    return abs(val.real) < tol and abs(val.imag - 1.0) < tol


# ── Sign propagation proof (N ≤ 7, all leaves = 1) ───────────────────────────

def analyze_up_to_n(max_n=7):
    results = {
        'max_n': max_n,
        'found_i': False,
        'witness': None,
        'loophole_found': False,
        'loophole_first_n': None,
        'loophole_example': None,
        'summary_by_n': {},
        'proof_status': None,
    }

    for n in range(1, max_n + 1):
        n_trees = 0
        n_real = 0
        n_complex = 0
        n_domain_error = 0
        n_loophole = 0  # trees where some y-arg ≤ 0
        found_i_this_n = False

        for tree in all_trees(n):
            n_trees += 1
            trace = []
            val = eval_tree(tree, trace)

            if val is None:
                n_domain_error += 1
                continue

            loophole_hit = any(step['y_is_nonpositive'] for step in trace)
            if loophole_hit:
                n_loophole += 1
                if results['loophole_first_n'] is None:
                    results['loophole_found'] = True
                    results['loophole_first_n'] = n
                    results['loophole_example'] = {
                        'n': n,
                        'root_value': str(val),
                        'trace': [
                            {k: str(v) for k, v in step.items()}
                            for step in trace
                        ],
                    }

            if is_i(val):
                found_i_this_n = True
                results['found_i'] = True
                results['witness'] = {'n': n, 'value': str(val)}

            if isinstance(val, complex) and val.imag != 0:
                n_complex += 1
            else:
                n_real += 1

        results['summary_by_n'][n] = {
            'total_trees': n_trees,
            'real_outputs': n_real,
            'complex_outputs': n_complex,
            'domain_errors': n_domain_error,
            'loophole_activations': n_loophole,
            'found_i': found_i_this_n,
        }

        print(f"N={n}: {n_trees} trees | real={n_real} complex={n_complex} "
              f"errors={n_domain_error} loophole={n_loophole} found_i={found_i_this_n}")

    # ── Determine proof status ────────────────────────────────────────────────
    if results['found_i']:
        results['proof_status'] = 'CONSTRUCTION_FOUND'
    elif not results['loophole_found']:
        results['proof_status'] = (
            'THEOREM_CANDIDATE: no loophole activated up to N={max_n}. '
            'All trees with leaves=1 stay real. i unreachable (conditional on N<={max_n}).'
        )
    else:
        results['proof_status'] = (
            f'LOOPHOLE_ACTIVE from N={results["loophole_first_n"]}: '
            f'some y-arguments become non-positive, injecting complex values. '
            f'But i was not produced up to N={max_n}. See S62 for focused attack.'
        )

    return results


# ── Key structural lemmas ─────────────────────────────────────────────────────

def prove_depth1_real():
    """
    Lemma: all N=1 trees with leaves in {1} evaluate to a positive real.

    Proof: the only N=1 tree is eml(1, 1) = exp(1) - ln(1) = e - 0 = e > 0.
    No complex values. ✓
    """
    val = eml(1.0, 1.0)
    assert isinstance(val, float) and val > 0, f"Unexpected: {val}"
    return {'lemma': 'depth1_real', 'value': val, 'proved': True}


def prove_all_depth1_values():
    """
    At N=1 the only tree is eml(1,1) = e.
    At N=2 the trees are: eml(eml(1,1), 1) and eml(1, eml(1,1)).
    Enumerate these explicitly.
    """
    results = {}
    e = math.e
    # N=1
    v1 = eml(1.0, 1.0)  # = e
    results['N=1'] = [v1]
    # N=2
    v2a = eml(eml(1.0, 1.0), 1.0)   # eml(e, 1) = exp(e) - 0 = exp(e)
    v2b = eml(1.0, eml(1.0, 1.0))   # eml(1, e) = exp(1) - ln(e) = e - 1
    results['N=2'] = [v2a, v2b]
    # All positive reals?
    all_positive = all(isinstance(v, float) and v > 0 for v in results['N=1'] + results['N=2'])
    results['all_positive_through_N2'] = all_positive
    return results


if __name__ == '__main__':
    print("=" * 60)
    print("S61 — i-Constructibility Analysis")
    print("=" * 60)
    print()

    # Structural check: N=1 and N=2 by hand
    lemma = prove_depth1_real()
    print(f"Lemma (N=1 real): {lemma}")

    depth12 = prove_all_depth1_values()
    print(f"N=1,2 values: {depth12}")
    print()

    # Full enumeration N=1..7
    print("Enumerating all trees with leaves=1, N=1..7 ...")
    print()
    data = analyze_up_to_n(max_n=7)

    print()
    print("=" * 60)
    print(f"PROOF STATUS: {data['proof_status']}")
    if data['loophole_found']:
        print(f"Loophole first appears at N={data['loophole_first_n']}")
        print(f"Example: {data['loophole_example']}")
    if data['found_i']:
        print(f"WITNESS: {data['witness']}")
    else:
        print("i = sqrt(-1) NOT FOUND in any tree up to N=7 with leaves=1")
    print("=" * 60)

    # Save results
    out_path = Path(__file__).parent.parent / 'results' / 's61_i_constructibility.json'
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")
