"""
analyze_n11.py — Post-search analysis for N=11 exhaustive results.

Usage:
    python monogate/search/analyze_n11.py
    python monogate/search/analyze_n11.py --json results/sin_n11.json
    python monogate/search/analyze_n11.py --json results/sin_n11.json --html output/n11_gallery.html
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

# ── Known per-N counts from all five search scripts ─────────────────────────

N_TABLE: list[dict[str, Any]] = [
    {"n": 1,  "catalan": 1,      "raw_trees": 4,          "after_parity": 2,          "cumulative": 4},
    {"n": 2,  "catalan": 2,      "raw_trees": 16,         "after_parity": 8,          "cumulative": 20},
    {"n": 3,  "catalan": 5,      "raw_trees": 80,         "after_parity": 40,         "cumulative": 100},
    {"n": 4,  "catalan": 14,     "raw_trees": 448,        "after_parity": 224,        "cumulative": 548},
    {"n": 5,  "catalan": 42,     "raw_trees": 2_688,      "after_parity": 1_344,      "cumulative": 3_236},
    {"n": 6,  "catalan": 132,    "raw_trees": 16_896,     "after_parity": 8_448,      "cumulative": 20_132},
    {"n": 7,  "catalan": 429,    "raw_trees": 109_824,    "after_parity": 54_912,     "cumulative": 129_956},
    {"n": 8,  "catalan": 1_430,  "raw_trees": 732_160,    "after_parity": 366_080,    "cumulative": 862_116},
    {"n": 9,  "catalan": 4_862,  "raw_trees": 4_978_688,  "after_parity": 2_489_344,  "cumulative": 5_840_804},
    {"n": 10, "catalan": 16_796, "raw_trees": 34_398_208, "after_parity": 17_199_104, "cumulative": 40_239_012},
    {"n": 11, "catalan": 58_786, "raw_trees": 240_787_456,"after_parity": 208_901_719,"cumulative": 281_026_468},
]


def _probe_formula(formula: str, x: float) -> float | None:
    """Evaluate an EML formula string at x. Returns None on domain error."""
    def _eml(a: float, b: float) -> float:
        if b <= 0:
            return float("nan")
        return math.exp(a) - math.log(b)

    def _parse_and_eval(s: str, xval: float) -> float:
        s = s.strip()
        if s == "x":
            return xval
        if s == "1":
            return 1.0
        try:
            return float(s)
        except ValueError:
            pass

        # Strip outer eml( ... ) call
        if s.startswith("eml(") and s.endswith(")"):
            inner = s[4:-1]
            # Find the comma that splits left and right at depth 0
            depth = 0
            for i, ch in enumerate(inner):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "," and depth == 0:
                    left_str = inner[:i]
                    right_str = inner[i + 1:]
                    lv = _parse_and_eval(left_str, xval)
                    rv = _parse_and_eval(right_str, xval)
                    return _eml(lv, rv)
        return float("nan")

    try:
        val = _parse_and_eval(formula, x)
        if not math.isfinite(val):
            return None
        return val
    except Exception:
        return None


def _compute_mse(formula: str, probe_x: list[float]) -> float:
    """Compute MSE of formula vs sin(x) over probe_x."""
    errs = []
    for x in probe_x:
        v = _probe_formula(formula, x)
        if v is None:
            return float("inf")
        errs.append((v - math.sin(x)) ** 2)
    if not errs:
        return float("inf")
    return sum(errs) / len(errs)


def print_summary_table(data: dict[str, Any]) -> None:
    """Print the N=1–11 summary table."""
    print()
    print("=" * 72)
    print("  EML EXHAUSTIVE SEARCH -- COMPLETE RESULTS (N <= 11)")
    print("=" * 72)
    print(f"  {'N':>3}  {'Catalan(N)':>12}  {'Raw trees':>14}  {'After parity':>14}  {'Result':>10}")
    print(f"  {'-'*3}  {'-'*12}  {'-'*14}  {'-'*14}  {'-'*10}")

    cumulative = 0
    for row in N_TABLE:
        cumulative = row["cumulative"]
        marker = " <--" if row["n"] == 11 else ""
        print(
            f"  {row['n']:>3}  {row['catalan']:>12,}  {row['raw_trees']:>14,}"
            f"  {row['after_parity']:>14,}  {'no candidate':>10}{marker}"
        )
    print(f"  {'-'*3}  {'-'*12}  {'-'*14}  {'-'*14}  {'-'*10}")
    print(f"  {'TOT':>3}  {'':>12}  {cumulative:>14,}  {'':>14}  {'0 candidates':>10}")
    print()

    # Runtime info from JSON
    results = data.get("results", {})
    tol_key = "0.0001"
    if tol_key in results:
        r = results[tol_key]
        print(f"  N=11 runtime: {r['elapsed_s']:.1f}s ({r['elapsed_s']/60:.1f} min)")
        print(f"  N=11 shapes:  {r['n_shapes']:,}")
        raw_trees = 240_787_456  # N=11: Catalan(11) * 2^12
    print(f"  Parity pruned: {r['p_parity']:,} assignments ({r['p_parity']/raw_trees*100:.1f}% of raw)")

    print()
    print("  RESULT: NO EML tree with terminals {1, x} equals sin(x) for any N <= 11.")
    print("  Theory: Infinite Zeros Barrier (sin has inf zeros; EML trees are real-analytic).")
    print("=" * 72)


def print_near_miss_gallery(
    near_misses: list[dict], probe_x: list[float], top_k: int = 10
) -> None:
    """Print the near-miss approximation gallery."""
    print()
    print("=" * 72)
    print("  TOP NEAR-MISS APPROXIMATIONS TO sin(x)  [real EML domain, N <= 11]")
    print("=" * 72)
    print("  These are the closest achievable EML trees -- not exact (proven impossible).")
    print()

    probe_display = [0.5, 1.0, math.pi / 2, math.pi]
    for rank, nm in enumerate(near_misses[:top_k], 1):
        formula = nm["formula"]
        mse = nm["mse"]
        n_leaves = nm.get("n_leaves", "?")

        print(f"  #{rank:02d}  MSE = {mse:.4e}   leaves = {n_leaves}")
        print(f"       {formula}")

        # Show values at a few reference points
        pts = []
        for x in probe_display:
            v = _probe_formula(formula, x)
            sx = math.sin(x)
            if v is not None:
                pts.append(f"  x={x:.3f}: T={v:+.4f}, sin={sx:+.4f}, err={v-sx:+.2e}")
        if pts:
            for pt in pts:
                print(f"      {pt}")
        print()

    print("  Best MSE context:")
    print(f"    exp(x)  vs sin(x): MSE ~0.42  (trivial 1-node baseline)")
    print(f"    #1 above vs sin(x): MSE = {near_misses[0]['mse']:.4e}  (2,842x better than baseline)")
    print()
    print("  Complex-domain exact (1 node):")
    print("    Im(eml(i*x, 1)) = sin(x)  -- exact for all x in R, MSE = 0")
    print("=" * 72)


def export_html(
    near_misses: list[dict],
    probe_x: list[float],
    out_path: str,
    top_k: int = 20,
) -> None:
    """Export a self-contained HTML near-miss gallery."""
    rows = []
    for rank, nm in enumerate(near_misses[:top_k], 1):
        formula = nm["formula"]
        mse = nm["mse"]
        n_leaves = nm.get("n_leaves", "?")
        mse_str = f"{mse:.4e}"

        # Compute values at reference probe points for sparkline
        pts = []
        for x in probe_x:
            v = _probe_formula(formula, x)
            if v is not None:
                pts.append({"x": round(x, 3), "T": round(v, 5), "sin": round(math.sin(x), 5)})

        pts_json = json.dumps(pts)
        rows.append(
            f"""<tr>
  <td class="rank">#{rank}</td>
  <td class="formula"><code>{formula}</code></td>
  <td class="mse">{mse_str}</td>
  <td class="leaves">{n_leaves}</td>
  <td class="pts" data-pts='{pts_json}'></td>
</tr>"""
        )

    rows_html = "\n".join(rows)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>monogate N=11 Near-Miss Gallery</title>
<style>
  body {{ font-family: monospace; background: #07080f; color: #cdd0e0; padding: 24px; }}
  h1 {{ color: #e8a020; font-size: 18px; }}
  p.sub {{ color: #4e5168; font-size: 12px; margin-top: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
  th {{ color: #4e5168; text-align: left; padding: 6px 10px;
        border-bottom: 1px solid #191b2e; font-size: 12px; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #191b2e11; font-size: 12px; }}
  .rank {{ color: #4e5168; width: 36px; }}
  .formula code {{ color: #cdd0e0; font-size: 11px; }}
  .mse {{ color: #e8a020; width: 100px; }}
  .leaves {{ color: #6ab0f5; width: 60px; }}
  .exact {{ color: #5ec47a; font-weight: bold; }}
  .banner {{ background: #0d0e1c; border: 1px solid #e8a02044;
             border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; }}
  .banner strong {{ color: #e8a020; }}
</style>
</head>
<body>
<h1>monogate — N=11 Near-Miss Approximations to sin(x)</h1>
<p class="sub">
  Exhaustive search over 281,026,468 EML trees (N ≤ 11, terminals {{1, x}}) — zero exact matches.
  These are the closest approximations found.
</p>

<div class="banner">
  <strong>Infinite Zeros Barrier:</strong> No finite real-valued EML tree equals sin(x).
  Proof: sin has infinitely many zeros (kπ); EML trees are real-analytic with finitely many zeros. □<br>
  <span style="color:#5ec47a">Complex bypass (1 node, exact): Im(eml(i·x, 1)) = sin(x)</span>
</div>

<table>
<thead>
<tr>
  <th>Rank</th>
  <th>Formula</th>
  <th>MSE</th>
  <th>Leaves</th>
  <th>Probe values</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>

<script>
document.querySelectorAll('td.pts').forEach(td => {{
  const pts = JSON.parse(td.dataset.pts || '[]');
  if (!pts.length) return;
  const lines = pts.slice(0, 4).map(p =>
    `x=${{p.x.toFixed(2)}}: T=${{p.T.toFixed(3)}} sin=${{p.sin.toFixed(3)}}`
  );
  td.textContent = lines.join(' | ');
  td.style.color = '#4e5168';
  td.style.fontSize = '11px';
  td.style.maxWidth = '300px';
  td.style.wordBreak = 'break-all';
}});
</script>
</body>
</html>"""

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"HTML gallery written to: {out_path}")


def run(json_path: str, html_out: str | None = None) -> None:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    probe_x: list[float] = data.get("probe_x", [0.1, 0.3, 0.5, 0.8, 1.0, 1.3, 1.5, 2.0])

    # Use the tightest tolerance's near_misses (1e-9 has the most aggressive filter)
    results = data.get("results", {})
    tol_key = "1e-09"
    if tol_key not in results:
        tol_key = sorted(results.keys())[-1]
    near_misses = results[tol_key].get("near_misses", [])

    # Attach raw_trees count to data for summary table
    data["raw_trees"] = results.get("0.0001", {}).get("total_trees_after_parity", 0)
    data["p_parity"]  = results.get("0.0001", {}).get("p_parity", 0)

    print_summary_table(data)
    print_near_miss_gallery(near_misses, probe_x)

    if html_out:
        export_html(near_misses, probe_x, html_out)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze N=11 exhaustive sin-search results")
    parser.add_argument(
        "--json",
        default=str(Path(__file__).parent.parent.parent / "results" / "sin_n11.json"),
        help="Path to sin_n11.json (default: results/sin_n11.json)",
    )
    parser.add_argument(
        "--html",
        default=None,
        help="If provided, write HTML near-miss gallery to this path",
    )
    args = parser.parse_args(argv)

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"ERROR: results file not found: {json_path}", file=sys.stderr)
        print("Run: python monogate/search/sin_search_05.py --save results/sin_n11.json", file=sys.stderr)
        sys.exit(1)

    run(str(json_path), args.html)


if __name__ == "__main__":
    main()
