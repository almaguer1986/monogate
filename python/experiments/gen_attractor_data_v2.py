"""
gen_attractor_data_v2.py — Phantom attractor deep-dive: 100 seeds, depth 3 & 4.
=================================================================================

Two experiments:

1. PHASE TRANSITION SWEEP
   depth = 3 and 4, lambda in [0, 0.001, 0.002, 0.003, 0.004, 0.005,
   0.008, 0.01, 0.02, 0.05], 20 seeds each, 1000 steps.
   Measures: convergence_rate (fraction of seeds reaching pi) vs lambda.
   Output: attractor_phase_transition.json

   KEY FINDING (2026-04-16):
   - depth=3: sharp phase transition at lambda_crit=0.001.  All seeds converge
     to the phantom attractor (3.170460) at lambda=0; 100% reach pi at lambda>=0.001.
   - depth=4: ALL seeds diverge to NaN/inf for ALL tested lambda values (0 to 0.05).
     Root cause: EMLTree(depth=4) has initial output ~10^13 to inf — the tower of
     15 nested eml nodes creates an exp() cascade that overflows float32/float64
     before training can begin.  This is the NUMERICAL OVERFLOW BARRIER:
     depth=3 (7 nodes, initial ~40K) is the practical training limit for naive
     EMLTree.  Depth=4 requires log-scale normalization or a different
     parameterization (not implemented in v0.4.0).

2. DETAILED TRAJECTORIES (optional, --full flag)
   depth=3 only (depth=4 not trainable), lambda = 0.0 and 0.005,
   100 seeds, 3000 steps.
   Output: attractor_data_v2.json  (100-seed update of attractor_data.json)

Usage:
    python experiments/gen_attractor_data_v2.py          # sweep only (~8 min)
    python experiments/gen_attractor_data_v2.py --full   # sweep + 100-seed detail (~25 min)
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent.parent))
from monogate.network import EMLTree

# ── Config ────────────────────────────────────────────────────────────────────

TARGET   = math.pi
LR       = 5e-3

# Phase-transition sweep
SWEEP_LAMBDAS = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.008, 0.01, 0.02, 0.05]
SWEEP_SEEDS   = 20
SWEEP_STEPS   = 1000
SWEEP_DEPTHS  = [3, 4]

# Detailed run (--full)
DETAIL_LAMBDAS = [0.0, 0.005]
DETAIL_SEEDS   = 100
DETAIL_STEPS   = 3000
DETAIL_DEPTHS  = [3, 4]

# Attractor values per depth (empirical; measured in gen_attractor_data.py)
ATTRACTORS = {
    3: 3.169642,
    4: None,   # will be measured during the sweep
}

OUT_SWEEP    = Path(__file__).parent.parent / "experiments" / "attractor_phase_transition.json"
OUT_DETAIL   = Path(__file__).parent.parent.parent / "explorer" / "public" / "attractor_data_v2.json"

# ── Core training ─────────────────────────────────────────────────────────────

def run_seed(seed: int, lam: float, depth: int, steps: int,
             record_every: int = 20) -> dict:
    """Train one EMLTree seed; return compact trajectory dict."""
    torch.manual_seed(seed * 17 + 3)
    model    = EMLTree(depth=depth)
    opt      = torch.optim.Adam(model.parameters(), lr=LR)
    target_t = torch.tensor(float(TARGET))

    loss_trace  = []
    value_trace = []

    for step in range(steps + 1):
        if step > 0:
            opt.zero_grad()
            try:
                pred     = model()
                raw_loss = (pred - target_t) ** 2
            except (ValueError, RuntimeError):
                if loss_trace:
                    loss_trace.append(loss_trace[-1])
                    value_trace.append(value_trace[-1])
                continue

            if not torch.isfinite(raw_loss):
                loss_trace.append(1000.0)
                value_trace.append(None)
                continue

            loss = raw_loss
            if lam > 0:
                penalty = sum((p - 1.0).abs().sum() for p in model.parameters())
                loss    = raw_loss + lam * penalty

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

        if step % record_every == 0:
            with torch.no_grad():
                try:
                    v = model().item()
                    l = (v - TARGET) ** 2
                except Exception:
                    v, l = float("nan"), 1000.0
            loss_trace.append(round(min(l, 1000.0), 8))
            value_trace.append(round(v, 8) if math.isfinite(v) else None)

    return {
        "seed":  seed,
        "lam":   lam,
        "depth": depth,
        "final_value": value_trace[-1],
        "final_loss":  loss_trace[-1],
        "loss":  loss_trace,
        "value": value_trace,
    }


def destiny(final_val: float | None, attractor: float | None) -> str:
    if final_val is None or not math.isfinite(final_val):
        return "diverged"
    dist_pi = abs(final_val - TARGET)
    if attractor is not None:
        dist_att = abs(final_val - attractor)
        return "pi" if dist_pi < dist_att else "attractor"
    # For unknown attractor, use threshold
    return "pi" if dist_pi < 0.05 else "other"


# ── Sweep experiment ──────────────────────────────────────────────────────────

def run_sweep() -> dict:
    print("=" * 64)
    print("  PHASE TRANSITION SWEEP")
    print(f"  depths={SWEEP_DEPTHS}  lambdas={len(SWEEP_LAMBDAS)}  "
          f"seeds={SWEEP_SEEDS}  steps={SWEEP_STEPS}")
    print("=" * 64)

    results = {}   # depth -> lambda -> {"convergence_rate": float, "mean_final": float}
    measured_attractors = dict(ATTRACTORS)

    for depth in SWEEP_DEPTHS:
        results[depth] = {}
        print(f"\n  depth={depth}")
        print(f"  {'lam':>8}  {'pi/'+str(SWEEP_SEEDS):>10}  {'mean_final':>12}  {'std_final':>10}")
        print("  " + "-" * 50)

        for lam in SWEEP_LAMBDAS:
            finals = []
            t0 = time.perf_counter()

            for seed in range(SWEEP_SEEDS):
                run = run_seed(seed, lam, depth, SWEEP_STEPS, record_every=50)
                if run["final_value"] is not None and math.isfinite(run["final_value"]):
                    finals.append(run["final_value"])

            # Measure attractor if lambda=0 and depth not already known
            if lam == 0.0 and measured_attractors.get(depth) is None and finals:
                measured_attractors[depth] = round(sum(finals) / len(finals), 6)

            att = measured_attractors.get(depth)
            n_pi = sum(1 for v in finals if abs(v - TARGET) < 0.01)
            conv_rate = n_pi / SWEEP_SEEDS
            mean_f = sum(finals) / len(finals) if finals else float("nan")
            std_f  = (sum((v - mean_f)**2 for v in finals) / len(finals))**0.5 if len(finals) > 1 else 0.0
            elapsed = time.perf_counter() - t0

            results[depth][lam] = {
                "convergence_rate": round(conv_rate, 4),
                "n_pi": n_pi,
                "n_seeds": SWEEP_SEEDS,
                "mean_final": round(mean_f, 6) if math.isfinite(mean_f) else None,
                "std_final": round(std_f, 6),
                "attractor": att,
            }
            print(f"  lam={lam:.4f}  {n_pi:>4}/{SWEEP_SEEDS}  "
                  f"mean={mean_f:>10.6f}  std={std_f:.4f}  ({elapsed:.1f}s)")

    # Find critical lambda per depth
    print()
    print("  Critical lambda (first lambda where convergence_rate > 0.5):")
    for depth in SWEEP_DEPTHS:
        critical = None
        for lam in SWEEP_LAMBDAS:
            if results[depth][lam]["convergence_rate"] > 0.5:
                critical = lam
                break
        att = measured_attractors.get(depth)
        print(f"    depth={depth}: lambda_crit={critical}  "
              f"attractor={att}")

    return {
        "config": {
            "depths": SWEEP_DEPTHS,
            "lambdas": SWEEP_LAMBDAS,
            "seeds": SWEEP_SEEDS,
            "steps": SWEEP_STEPS,
            "lr": LR,
            "target": TARGET,
        },
        "attractors": {str(d): v for d, v in measured_attractors.items()},
        "results": {str(d): {str(l): v for l, v in lv.items()}
                    for d, lv in results.items()},
    }


# ── Detailed trajectories ─────────────────────────────────────────────────────

def run_detail(measured_attractors: dict) -> dict:
    print()
    print("=" * 64)
    print("  DETAILED TRAJECTORIES (100 seeds)")
    print(f"  depths={DETAIL_DEPTHS}  lambdas={DETAIL_LAMBDAS}  "
          f"seeds={DETAIL_SEEDS}  steps={DETAIL_STEPS}")
    print("=" * 64)

    all_runs = []
    total = len(DETAIL_DEPTHS) * len(DETAIL_LAMBDAS) * DETAIL_SEEDS
    done  = 0
    t0    = time.perf_counter()

    for depth in DETAIL_DEPTHS:
        att = measured_attractors.get(depth) or measured_attractors.get(str(depth))
        for lam in DETAIL_LAMBDAS:
            n_pi = n_att = n_div = 0
            for seed in range(DETAIL_SEEDS):
                run = run_seed(seed, lam, depth, DETAIL_STEPS, record_every=20)
                dest = destiny(run["final_value"], att)
                run["destiny"] = dest
                all_runs.append(run)
                done += 1
                if dest == "pi":      n_pi  += 1
                elif dest == "other": n_div += 1
                else:                 n_att += 1

                elapsed = time.perf_counter() - t0
                eta = elapsed / done * (total - done) if done < total else 0
                sys.stdout.write(
                    f"\r  depth={depth} lam={lam:.3f} seed {seed:03d}/{DETAIL_SEEDS-1}  "
                    f"[pi:{n_pi} att:{n_att} div:{n_div}]  "
                    f"eta {eta:.0f}s    "
                )
                sys.stdout.flush()
            print()
            print(f"  depth={depth} lam={lam:.3f}: "
                  f"pi={n_pi}/{DETAIL_SEEDS}  att={n_att}/{DETAIL_SEEDS}  "
                  f"div={n_div}/{DETAIL_SEEDS}")

    n_points = DETAIL_STEPS // 20 + 1
    return {
        "meta": {
            "n_seeds":     DETAIL_SEEDS,
            "steps":       DETAIL_STEPS,
            "record_every": 20,
            "n_points":    n_points,
            "depths":      DETAIL_DEPTHS,
            "lambdas":     DETAIL_LAMBDAS,
            "target":      TARGET,
            "attractors":  {str(d): v for d, v in measured_attractors.items()},
        },
        "runs": all_runs,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    full = "--full" in sys.argv

    t0 = time.perf_counter()

    # Sweep (always)
    sweep_data = run_sweep()
    with open(OUT_SWEEP, "w") as f:
        json.dump(sweep_data, f, indent=2)
    print(f"\nSweep saved -> {OUT_SWEEP} ({OUT_SWEEP.stat().st_size/1024:.1f} KB)")

    if full:
        measured_attractors = sweep_data["attractors"]
        detail_data = run_detail(measured_attractors)
        OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_DETAIL, "w") as f:
            json.dump(detail_data, f, separators=(",", ":"))
        print(f"Detail saved -> {OUT_DETAIL} ({OUT_DETAIL.stat().st_size/1024:.1f} KB)")

    print(f"\nTotal time: {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
