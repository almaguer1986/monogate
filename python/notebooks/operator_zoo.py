"""
operator_zoo.py  --  Operator leaderboard across multiple regression targets.

Run:
    cd D:/monogate
    python python/notebooks/operator_zoo.py [--plot]

Pass --plot to save a matplotlib figure to operator_zoo_results.png.

Operators compared
------------------
  EML       standard gate (exp-minus-log), depth=3
  EDL       raw gate (exp-div-log), depth=3  -- kept for comparison
  EDL_safe  EDL with safe right-domain shift, depth=3
  EXL       exp-times-log gate, depth=3
  Hybrid    EXL inner + EML root, depth=3

Targets
-------
  sin(x)     x in [-pi, pi]
  cos(x)     x in [-pi, pi]
  x^3        x in [-2, 2]
  x^2 - x    x in [-2, 2]
  exp(x)     x in [-2, 2]
  poly4      x^4 - 2x^2 + 1  on [-2, 2]
  sqrt(x)    x in [0.1, 4]

Metrics (per operator x target, 5 restarts)
-------------------------------------------
  med_mse    median final MSE across restarts
  min_mse    best final MSE across restarts
  conv%      % restarts reaching MSE < THRESHOLD
  nan%       % training steps that produced non-finite loss
  stability  % of depth-5 random-init forward passes that are finite

Output
------
  Prints a Markdown leaderboard table.
  Writes operator_zoo_results.png if --plot passed.
"""

import math
import statistics
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

from monogate.network import EMLNetwork, HybridNetwork, fit
from monogate.torch_ops import edl_op, edl_op_safe, exl_op

# ── Config ────────────────────────────────────────────────────────────────────

SEED        = 7
N_RESTARTS  = 5
STEPS       = 1200
LR          = 3e-3
THRESHOLD   = 5e-4       # MSE threshold for convergence
DEPTH       = 3
N_POINTS    = 256
STRESS_N    = 30         # random inits for stability measurement
STRESS_DEPTH = 5

torch.manual_seed(SEED)

DO_PLOT = "--plot" in sys.argv

# ── Operator definitions ──────────────────────────────────────────────────────

def _make_model(op_key):
    if op_key == "EML":
        return EMLNetwork(in_features=1, depth=DEPTH, op_func=None)
    if op_key == "EDL":
        return EMLNetwork(in_features=1, depth=DEPTH, op_func=edl_op)
    if op_key == "EDL_safe":
        return EMLNetwork(in_features=1, depth=DEPTH, op_func=edl_op_safe)
    if op_key == "EXL":
        return EMLNetwork(in_features=1, depth=DEPTH, op_func=exl_op)
    if op_key == "Hybrid":
        return HybridNetwork(in_features=1, depth=DEPTH)
    raise ValueError(f"Unknown operator: {op_key!r}")


OP_KEYS = ["EML", "EDL", "EDL_safe", "EXL", "Hybrid"]

# ── Target functions ──────────────────────────────────────────────────────────

TARGETS = [
    ("sin(x)",       math.sin,              -math.pi,  math.pi),
    ("cos(x)",       math.cos,              -math.pi,  math.pi),
    ("x^3",          lambda x: x**3,        -2.0,      2.0),
    ("x^2-x",        lambda x: x**2 - x,   -2.0,      2.0),
    ("exp(x)",       math.exp,              -2.0,      2.0),
    ("poly4",        lambda x: x**4-2*x**2+1, -2.0,   2.0),
    ("sqrt(x)",      math.sqrt,              0.1,      4.0),
]

# ── Data generation ───────────────────────────────────────────────────────────

def _make_data(fn, lo, hi, n=N_POINTS):
    x = torch.linspace(lo, hi, n).unsqueeze(1)
    y = torch.tensor([fn(xi.item()) for xi in x.squeeze(1)])
    return x, y


# ── Single run ────────────────────────────────────────────────────────────────

def _run_once(op_key, x, y, seed_offset=0):
    torch.manual_seed(SEED + seed_offset * 17)
    model = _make_model(op_key)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    best_mse  = float("inf")
    conv_step = None
    nan_steps = 0

    for step in range(1, STEPS + 1):
        opt.zero_grad()
        try:
            pred = model(x)
            loss = F.mse_loss(pred, y)
        except Exception:
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
        if not math.isfinite(final_mse):
            final_mse = float("inf")
    except Exception:
        final_mse = float("inf")

    return final_mse, best_mse, conv_step, nan_steps / STEPS


# ── Per-operator stability (depth-5 random init) ──────────────────────────────

def _measure_stability(op_key):
    x = torch.linspace(0.1, 3.0, 64).unsqueeze(1)
    ok = 0
    for i in range(STRESS_N):
        torch.manual_seed(i * 31 + 3)
        model = _make_model(op_key)
        # Override depth with STRESS_DEPTH by building a fresh network
        if op_key == "Hybrid":
            m = HybridNetwork(in_features=1, depth=STRESS_DEPTH)
        else:
            op_func = {"EML": None, "EDL": edl_op, "EDL_safe": edl_op_safe,
                       "EXL": exl_op}[op_key]
            m = EMLNetwork(in_features=1, depth=STRESS_DEPTH, op_func=op_func)
        with torch.no_grad():
            for p in m.parameters():
                p.data.normal_(0.0, 0.5)
        try:
            out = m(x)
            if torch.isfinite(out).all():
                ok += 1
        except Exception:
            pass
    return ok / STRESS_N


# ── Multi-restart benchmark ────────────────────────────────────────────────────

def benchmark_op_target(op_key, x, y):
    finals, bests, conv_steps, nan_rates = [], [], [], []
    for i in range(N_RESTARTS):
        f, b, c, n = _run_once(op_key, x, y, seed_offset=i)
        finals.append(f)
        bests.append(b)
        conv_steps.append(c)
        nan_rates.append(n)
    converged = [c for c in conv_steps if c is not None]
    return {
        "med_mse":    statistics.median(finals),
        "min_mse":    min(finals),
        "conv_rate":  len(converged) / N_RESTARTS,
        "nan_rate":   statistics.median(nan_rates),
    }


# ── Markdown table helpers ────────────────────────────────────────────────────

def _fmt_mse(v):
    if v == float("inf"):
        return "inf"
    if v < 1e-10:
        return f"{v:.1e}"
    return f"{v:.3e}"


def _best_mask(col_vals):
    """Return set of indices that are the finite minimum."""
    finite = [v for v in col_vals if math.isfinite(v)]
    if not finite:
        return set()
    best = min(finite)
    return {i for i, v in enumerate(col_vals) if v == best}


def print_leaderboard(results, stability):
    """
    results: dict  target_name -> dict op_key -> {med_mse, min_mse, conv_rate, nan_rate}
    stability: dict op_key -> float (0..1)
    """
    targets   = [t[0] for t in TARGETS]
    col_width = 10

    # ── Table 1: Median MSE ───────────────────────────────────────────────────
    print("\n## Operator Zoo — Median Final MSE\n")
    print("(lower is better; **bold** = best per target; `inf` = all runs diverged)\n")

    hdr = "| Operator |" + "".join(f" {t:<{col_width}} |" for t in targets)
    sep = "| --- |" + "".join([f" --- |"] * len(targets))
    print(hdr)
    print(sep)

    for op in OP_KEYS:
        col_vals  = [results[t].get(op, {}).get("med_mse", float("inf")) for t in targets]
        best_idxs = []
        for t in targets:
            col = [results[t].get(k, {}).get("med_mse", float("inf")) for k in OP_KEYS]
            bm  = _best_mask(col)
            op_idx = OP_KEYS.index(op)
            best_idxs.append(op_idx in bm)

        cells = []
        for i, (v, is_best) in enumerate(zip(col_vals, best_idxs)):
            s = _fmt_mse(v)
            cells.append(f"**{s}**" if is_best else s)
        print("| " + op + " |" + "".join(f" {c:<{col_width}} |" for c in cells))

    # ── Table 2: Convergence % ────────────────────────────────────────────────
    print(f"\n\n## Convergence Rate  (MSE < {THRESHOLD:.0e}, {N_RESTARTS} restarts)\n")
    print(hdr)
    print(sep)
    for op in OP_KEYS:
        cells = []
        for t in targets:
            v = results[t].get(op, {}).get("conv_rate", 0.0)
            cells.append(f"{v:.0%}")
        print("| " + op + " |" + "".join(f" {c:<{col_width}} |" for c in cells))

    # ── Table 3: NaN rate + stability ─────────────────────────────────────────
    print(f"\n\n## NaN Rate (training steps) + Deep Stability (depth-{STRESS_DEPTH})\n")
    print("| Operator | avg NaN% | deep ok% |")
    print("| --- | --- | --- |")
    for op in OP_KEYS:
        nan_vals = [results[t].get(op, {}).get("nan_rate", 0.0) for t in targets]
        avg_nan  = sum(nan_vals) / len(nan_vals)
        stab     = stability.get(op, float("nan"))
        print(f"| {op} | {avg_nan:.1%} | {stab:.0%} |")


# ── Optional matplotlib plot ──────────────────────────────────────────────────

def save_plot(results, stability):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("\n[plot skipped: matplotlib not installed]")
        return

    targets = [t[0] for t in TARGETS]
    n_t = len(targets)
    n_op = len(OP_KEYS)
    x_pos = np.arange(n_t)
    width = 0.15
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: log10(median MSE) per operator x target
    ax = axes[0]
    for i, (op, color) in enumerate(zip(OP_KEYS, colors)):
        vals = []
        for t in targets:
            v = results[t].get(op, {}).get("med_mse", float("inf"))
            vals.append(min(math.log10(v + 1e-15), 2.0) if math.isfinite(v) else 2.0)
        ax.bar(x_pos + i * width, vals, width, label=op, color=color, alpha=0.85)
    ax.set_xticks(x_pos + width * (n_op - 1) / 2)
    ax.set_xticklabels(targets, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("log10(median MSE)")
    ax.set_title("Median Final MSE (lower = better)")
    ax.legend(fontsize=8)
    ax.set_ylim(-6, 2.5)
    ax.axhline(math.log10(THRESHOLD), ls="--", color="gray", lw=0.8, label="threshold")

    # Panel 2: deep stability bar
    ax2 = axes[1]
    stab_vals = [stability.get(op, 0.0) * 100 for op in OP_KEYS]
    ax2.bar(OP_KEYS, stab_vals, color=colors, alpha=0.85)
    ax2.set_ylabel(f"% finite (depth-{STRESS_DEPTH} random init)")
    ax2.set_title(f"Deep Stability (depth={STRESS_DEPTH})")
    ax2.set_ylim(0, 105)
    for i, v in enumerate(stab_vals):
        ax2.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9)

    fig.tight_layout()
    out = "python/notebooks/operator_zoo_results.png"
    fig.savefig(out, dpi=130)
    print(f"\n[plot saved to {out}]")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Operator Zoo — {len(OP_KEYS)} operators x {len(TARGETS)} targets")
    print(f"depth={DEPTH}  restarts={N_RESTARTS}  steps={STEPS}  lr={LR}")
    print("=" * 60)

    # Stability scores (precompute, independent of targets)
    print("\nMeasuring deep stability...", end="", flush=True)
    stability = {}
    for op in OP_KEYS:
        stability[op] = _measure_stability(op)
        print(f" {op}={stability[op]:.0%}", end="", flush=True)
    print()

    # Regression benchmarks
    results = {t[0]: {} for t in TARGETS}
    for name, fn, lo, hi in TARGETS:
        x, y = _make_data(fn, lo, hi)
        print(f"\n  {name}", end="", flush=True)
        for op in OP_KEYS:
            r = benchmark_op_target(op, x, y)
            results[name][op] = r
            sym = "*" if r["conv_rate"] > 0 else ("!" if r["nan_rate"] > 0.5 else ".")
            print(sym, end="", flush=True)
    print()

    print_leaderboard(results, stability)

    if DO_PLOT:
        save_plot(results, stability)

    print("\n\nDone.")
