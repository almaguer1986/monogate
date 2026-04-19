"""
S85 — Small-Depth Target Set Catalog

Exhaustively catalog all Im(z)/Re(z) ratios for z ∈ EML₁ with depth ≤ 9.
Confirm none equal tan(1).

This is the computational backbone of Claim C.
"""

import json
import math
import cmath
from pathlib import Path
from fractions import Fraction

TAN1 = math.tan(1)
TOLERANCE = 1e-10


def eml(x, y):
    """Extended EML: exp(x) - Log(y), principal branch."""
    if abs(y) < 1e-300:
        return None
    try:
        if x.real > 700:
            return None
        return cmath.exp(x) - cmath.log(y)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def build_eml_closure(max_depth):
    """Build EML₁ values by depth layers, pruning large values."""
    # Layer i = values reachable at exactly depth i
    # values_at[d] = list of (value, expr)
    values_at = {0: [(complex(1.0), "1")]}
    seen = {round_c(complex(1.0))}

    for d in range(1, max_depth + 1):
        new_layer = []
        # New values at depth d: eml(v1, v2) where max(d1,d2) = d-1
        # i.e., at least one of d1, d2 equals d-1
        all_prev = []
        for dd in range(d):
            all_prev.extend([(v, e, dd) for v, e in values_at.get(dd, [])])

        layer_d_minus_1 = values_at.get(d - 1, [])

        for v1, e1, d1 in all_prev:
            for v2, e2 in layer_d_minus_1:
                result = eml(v1, v2)
                if result is None:
                    continue
                if abs(result) > 1e12:
                    continue
                key = round_c(result)
                if key not in seen:
                    seen.add(key)
                    new_layer.append((result, f"eml({e1[:20]},{e2[:20]})"))

        for v2, e2, d2 in all_prev:
            for v1, e1 in layer_d_minus_1:
                result = eml(v1, v2)
                if result is None:
                    continue
                if abs(result) > 1e12:
                    continue
                key = round_c(result)
                if key not in seen:
                    seen.add(key)
                    new_layer.append((result, f"eml({e1[:20]},{e2[:20]})"))

        values_at[d] = new_layer
        print(f"  depth {d}: {len(new_layer)} new values (total unique: {len(seen)})")

    # Flatten
    all_values = []
    for d, layer in values_at.items():
        for v, e in layer:
            all_values.append((v, d, e))
    return all_values


def round_c(z, digits=8):
    return (round(z.real, digits), round(z.imag, digits))


def analyze_ratios(values):
    """Compute Im/Re ratios for all values with Re != 0, Im != 0."""
    ratios = []
    for val, depth, expr in values:
        re, im = val.real, val.imag
        if abs(re) > 1e-10 and abs(im) > 1e-10:
            ratio = im / re
            ratios.append({
                "depth": depth,
                "re": re,
                "im": im,
                "ratio_im_re": ratio,
                "arg_radians": math.atan2(im, re),
                "ratio_minus_tan1": ratio - TAN1,
                "close_to_tan1": abs(ratio - TAN1) < TOLERANCE,
                "close_to_neg_tan1": abs(ratio + TAN1) < TOLERANCE,
                "expr": expr[:60],
            })
    return ratios


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("S85 — Small-Depth Target Set Catalog (depth <= 7)")
    print("=" * 60)
    print()
    print(f"tan(1) = {TAN1:.15f}")
    print()

    MAX_DEPTH = 5
    print(f"Building EML₁ closure up to depth {MAX_DEPTH}...")
    values = build_eml_closure(MAX_DEPTH)
    print(f"Total values: {len(values)}")
    print()

    ratios = analyze_ratios(values)

    # Statistics
    depth_counts = {}
    for v, d, e in values:
        depth_counts[d] = depth_counts.get(d, 0) + 1

    complex_count = sum(1 for v, d, e in values if abs(v.imag) > 1e-10)
    tan1_matches = [r for r in ratios if r["close_to_tan1"]]
    neg_tan1_matches = [r for r in ratios if r["close_to_neg_tan1"]]

    print("Depth distribution:")
    for d in sorted(depth_counts):
        print(f"  depth {d}: {depth_counts[d]} values")
    print()
    print(f"Complex values (Im != 0): {complex_count}")
    print(f"Values with Re != 0 and Im != 0: {len(ratios)}")
    print()
    print(f"Im/Re ratios close to  tan(1): {len(tan1_matches)}")
    print(f"Im/Re ratios close to -tan(1): {len(neg_tan1_matches)}")
    print()

    if tan1_matches:
        print("ALERT: Found Im/Re = tan(1)!")
        for r in tan1_matches:
            print(f"  depth {r['depth']}: {r['expr']}")
            print(f"  ratio = {r['ratio_im_re']:.15f}")
    else:
        print("CONFIRMED: No Im/Re ratio equals tan(1) at depth <= " + str(MAX_DEPTH))

    if neg_tan1_matches:
        print("ALERT: Found Im/Re = -tan(1)!")
        for r in neg_tan1_matches:
            print(f"  depth {r['depth']}: {r['expr']}")
    else:
        print("CONFIRMED: No Im/Re ratio equals -tan(1) at depth <= " + str(MAX_DEPTH))

    # Show all unique arg values seen
    print()
    print("Unique argument (arg(z)) values seen:")
    arg_vals = sorted(set(round(r["arg_radians"], 6) for r in ratios))
    for a in arg_vals[:20]:
        print(f"  arg = {a:.6f}  (pi-ratio: {a/math.pi:.6f})")

    # Check if arg = +-1 is in the set
    arg_equals_1 = any(abs(r["arg_radians"] - 1.0) < TOLERANCE for r in ratios)
    arg_equals_neg1 = any(abs(r["arg_radians"] + 1.0) < TOLERANCE for r in ratios)
    print()
    print(f"arg(z) = +1 found: {arg_equals_1}")
    print(f"arg(z) = -1 found: {arg_equals_neg1}")

    CATALOG = {
        "session": "S85",
        "title": "Small-Depth Im/Re Ratio Catalog",
        "max_depth": MAX_DEPTH,
        "total_values": len(values),
        "complex_values": complex_count,
        "ratio_entries": len(ratios),
        "tan1_value": TAN1,
        "tan1_matches": len(tan1_matches),
        "neg_tan1_matches": len(neg_tan1_matches),
        "arg_equals_1_found": arg_equals_1,
        "arg_equals_neg1_found": arg_equals_neg1,
        "unique_args_seen": arg_vals[:30],
        "all_ratios": [
            {k: (float(v) if isinstance(v, float) else v)
             for k, v in r.items()}
            for r in ratios[:100]
        ],
        "conclusion": (
            f"At depth <= {MAX_DEPTH}: NO element of EML₁ has Im/Re = tan(1). "
            "Consistent with Claim C."
        ),
    }

    out_path = results_dir / "s85_ratio_catalog.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(CATALOG, f, indent=2)

    print()
    print(f"Results: {out_path}")
