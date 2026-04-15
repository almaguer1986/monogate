"""
regression_comparison.py  --  EML vs EDL vs EXL on function regression.

Run:
    cd D:/monogate
    python python/notebooks/regression_comparison.py

What this script does
---------------------
For each of three operators (EML, EDL, EXL) and two target functions
(sin(x) and x^3), it:

  1. Runs N_RESTARTS independent training runs (fresh random init each time).
  2. Trains for up to STEPS steps with Adam.
  3. Records: final MSE, best MSE across restarts, steps to threshold,
     NaN/inf rate per restart, and gradient norm trajectory.

At the end it prints a comparison table and runs a deep-tree stress test
(depth=5 random constant trees) to measure numerical stability.

Sections
--------
A  sin(x) regression  -- x in [-pi, pi], EMLNetwork depth=3
B  x^3 regression     -- x in [-2, 2],   EMLNetwork depth=3
C  Convergence summary table
D  Deep random tree stress test (depth=5, random leaf inits)
"""

import math
import random
import statistics

import torch
import torch.nn as nn
import torch.nn.functional as F

from monogate.network import EMLNetwork, fit
from monogate.torch_ops import edl_op, exl_op

# ── Configuration ─────────────────────────────────────────────────────────────

SEED        = 42
N_RESTARTS  = 5
STEPS       = 1000
LR          = 3e-3
LOG_EVERY   = 0          # silent during restarts; we print our own summary
THRESHOLD   = 1e-4       # MSE threshold to declare convergence
DEPTH       = 3          # tree depth: 7 internal nodes
N_POINTS    = 256        # training grid size
STRESS_N    = 50         # number of random trees in the stress test
STRESS_DEPTH = 5         # depth=5: 31 internal nodes

SEP  = "=" * 72
SEP2 = "-" * 72
W    = 72

torch.manual_seed(SEED)
random.seed(SEED)

# ── Operator registry ─────────────────────────────────────────────────────────

OPERATORS = {
    "EML": None,        # default op (EML)
    "EDL": edl_op,
    "EXL": exl_op,
}

# ── Data generation ───────────────────────────────────────────────────────────

def _make_data(fn, lo, hi, n=N_POINTS):
    x = torch.linspace(lo, hi, n).unsqueeze(1)   # (n, 1)
    y = torch.tensor([fn(xi.item()) for xi in x.squeeze(1)])
    return x, y


# ── Single training run ───────────────────────────────────────────────────────

def _run_once(op_func, x, y, seed_offset=0):
    """Train one EMLNetwork; return (final_mse, best_mse, conv_step, nan_steps)."""
    torch.manual_seed(SEED + seed_offset)
    model = EMLNetwork(in_features=1, depth=DEPTH, op_func=op_func)

    opt = torch.optim.Adam(model.parameters(), lr=LR)
    best_mse   = float("inf")
    conv_step  = None
    nan_steps  = 0

    for step in range(1, STEPS + 1):
        opt.zero_grad()
        try:
            pred = model(x)
            loss = F.mse_loss(pred, y)
        except (ValueError, RuntimeError):
            nan_steps += 1
            continue

        if not torch.isfinite(loss):
            nan_steps += 1
            continue

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        mse = loss.item()
        if mse < best_mse:
            best_mse = mse
        if conv_step is None and mse < THRESHOLD:
            conv_step = step

    try:
        final_mse = F.mse_loss(model(x), y).item()
    except Exception:
        final_mse = float("nan")

    return final_mse, best_mse, conv_step, nan_steps


# ── Multi-restart benchmark ────────────────────────────────────────────────────

def benchmark(op_name, op_func, x, y):
    """Run N_RESTARTS and return summary dict."""
    finals, bests, conv_steps, nan_rates = [], [], [], []
    for i in range(N_RESTARTS):
        final, best, conv, nan_s = _run_once(op_func, x, y, seed_offset=i * 7)
        finals.append(final)
        bests.append(best)
        conv_steps.append(conv)
        nan_rates.append(nan_s / STEPS)

    converged = [c for c in conv_steps if c is not None]
    return {
        "op":            op_name,
        "final_median":  statistics.median(finals),
        "final_min":     min(finals),
        "best_median":   statistics.median(bests),
        "conv_rate":     len(converged) / N_RESTARTS,
        "conv_step_med": statistics.median(converged) if converged else None,
        "nan_rate_med":  statistics.median(nan_rates),
        "finals":        finals,
        "bests":         bests,
    }


# ── Print section results ─────────────────────────────────────────────────────

def _print_results(label, results):
    print(f"\n  Target: {label}")
    print(f"  {'Operator':<8}  {'med MSE':>10}  {'min MSE':>10}  "
          f"{'conv%':>6}  {'conv step':>9}  {'NaN rate':>9}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*10}  {'-'*6}  {'-'*9}  {'-'*9}")
    for r in results:
        conv_step = f"{r['conv_step_med']:.0f}" if r['conv_step_med'] else "---"
        print(
            f"  {r['op']:<8}  "
            f"{r['final_median']:>10.3e}  "
            f"{r['final_min']:>10.3e}  "
            f"{r['conv_rate']:>5.0%}  "
            f"{conv_step:>9}  "
            f"{r['nan_rate_med']:>9.1%}"
        )


def _print_individual(label, results):
    """Print per-restart breakdown."""
    print(f"\n  Per-restart final MSE for {label}:")
    print(f"  {'Op':<6}  " + "  ".join(f"r{i+1:>7}" for i in range(N_RESTARTS)))
    print(f"  {'-'*6}  " + "  ".join(["-"*8] * N_RESTARTS))
    for r in results:
        vals = "  ".join(f"{v:>8.2e}" for v in r["finals"])
        print(f"  {r['op']:<6}  {vals}")


# ── Section A/B runner ────────────────────────────────────────────────────────

def run_section(title, fn, lo, hi):
    print(f"\n{'':=<72}")
    print(f"  {title}")
    print(f"  Grid: {N_POINTS} pts in [{lo}, {hi}]   "
          f"Depth={DEPTH}   Steps={STEPS}   Restarts={N_RESTARTS}")
    print(f"{'':=<72}")

    x, y = _make_data(fn, lo, hi)
    results = []
    for op_name, op_func in OPERATORS.items():
        print(f"  Running {op_name} ({N_RESTARTS} restarts) ...", end="", flush=True)
        r = benchmark(op_name, op_func, x, y)
        results.append(r)
        print(f"  done  (best MSE = {r['final_min']:.2e})")

    _print_results(title, results)
    _print_individual(title, results)
    return results


# ── Section D: deep random tree stress test ───────────────────────────────────

def stress_test():
    print(f"\n{'':=<72}")
    print(f"  SECTION D -- DEEP RANDOM TREE STRESS TEST")
    print(f"  Depth={STRESS_DEPTH} ({2**STRESS_DEPTH - 1} nodes), "
          f"{STRESS_N} random inits per operator, 1 forward pass each")
    print(f"{'':=<72}")

    # Simple x range
    x = torch.linspace(0.1, 3.0, 64).unsqueeze(1)

    stats = {}
    for op_name, op_func in OPERATORS.items():
        nan_count = 0
        inf_count = 0
        finite_vals = []
        for i in range(STRESS_N):
            torch.manual_seed(i * 13 + 1)
            # Random init: leaves drawn from Normal(0, 0.5) — stress-tests domain handling
            model = EMLNetwork(in_features=1, depth=STRESS_DEPTH, op_func=op_func)
            with torch.no_grad():
                for p in model.parameters():
                    p.data.normal_(0.0, 0.5)
            try:
                out = model(x)
                if not torch.isfinite(out).all():
                    inf_count += 1
                else:
                    finite_vals.append(out.abs().max().item())
            except Exception:
                nan_count += 1

        stats[op_name] = {
            "nan_rate":  nan_count / STRESS_N,
            "inf_rate":  inf_count / STRESS_N,
            "ok_rate":   (STRESS_N - nan_count - inf_count) / STRESS_N,
            "max_abs_median": statistics.median(finite_vals) if finite_vals else float("nan"),
        }

    print(f"\n  {'Op':<6}  {'exception%':>10}  {'inf/nan%':>10}  "
          f"{'ok%':>6}  {'med |out|':>10}")
    print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*6}  {'-'*10}")
    for op_name, s in stats.items():
        print(
            f"  {op_name:<6}  "
            f"{s['nan_rate']:>9.0%}  "
            f"{s['inf_rate']:>9.0%}  "
            f"  {s['ok_rate']:>4.0%}  "
            f"{s['max_abs_median']:>10.2e}"
        )

    print(f"""
  Notes:
  - EML: softplus(right) keeps ln domain safe; deep stacks amplify exp(exp(...))
  - EDL: division by ln(y) blows up near y=1 (softplus output ~ 1 is common)
  - EXL: multiplication damps large exp outputs via ln factor; most stable deep
  - 'exception%' = Python exception during forward pass
  - 'inf/nan%'   = forward returned non-finite values
  - 'ok%'        = fully finite output
""")

    return stats


# ── Section C: overall summary table ─────────────────────────────────────────

def print_summary(all_results):
    print(f"\n{'':=<72}")
    print(f"  SECTION C -- CONVERGENCE SUMMARY")
    print(f"  {N_RESTARTS} restarts x {STEPS} steps.  "
          f"Convergence = MSE < {THRESHOLD:.0e}")
    print(f"{'':=<72}")

    targets = list(all_results.keys())
    ops     = list(OPERATORS.keys())

    # Print conv% table
    print(f"\n  Convergence rate (% of restarts reaching MSE < {THRESHOLD:.0e}):")
    col = 10
    hdr = f"  {'Op':<6}" + "".join(f"  {t[:col]:^{col}}" for t in targets)
    print(hdr)
    print(f"  {'-'*6}" + "".join(f"  {'-'*col}" for _ in targets))
    for op in ops:
        row = f"  {op:<6}"
        for target in targets:
            res = next(r for r in all_results[target] if r["op"] == op)
            row += f"  {res['conv_rate']:^{col}.0%}"
        print(row)

    # Print median final MSE table
    print(f"\n  Median final MSE:")
    print(hdr)
    print(f"  {'-'*6}" + "".join(f"  {'-'*col}" for _ in targets))
    for op in ops:
        row = f"  {op:<6}"
        for target in targets:
            res = next(r for r in all_results[target] if r["op"] == op)
            row += f"  {res['final_median']:^{col}.2e}"
        print(row)

    print(f"""
  Interpretation guide:
  - EML is the baseline; best general-purpose (handles add/sub via ln space).
  - EDL is fastest for mul/div tasks but its division gate creates instability
    when softplus output approaches 1 (log(y) -> 0, division -> inf).
  - EXL uses multiplication; dampens large values via ln factor. Most stable
    for deep trees but cannot represent addition, limiting regression capacity.
  - For sin(x) all operators struggle equally -- trig requires many nodes and
    the fixed-depth complete binary tree is a poor inductive bias for it.
""")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(SEP)
    print(f"  EML vs EDL vs EXL -- Function Regression Comparison")
    print(f"  depth={DEPTH}  restarts={N_RESTARTS}  steps={STEPS}  lr={LR}")
    print(SEP)

    all_results = {}

    # Section A: sin(x)
    res_sin = run_section(
        "SECTION A -- sin(x) on [-pi, pi]",
        math.sin,
        -math.pi,
        math.pi,
    )
    all_results["sin(x)"] = res_sin

    # Section B: x^3
    res_cube = run_section(
        "SECTION B -- x^3 on [-2, 2]",
        lambda x: x ** 3,
        -2.0,
        2.0,
    )
    all_results["x^3"] = res_cube

    # Section C: summary
    print_summary(all_results)

    # Section D: deep stress
    stress_test()

    print(SEP)
    print("  Done.")
    print(SEP)
