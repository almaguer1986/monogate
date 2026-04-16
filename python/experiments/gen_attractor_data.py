"""
gen_attractor_data.py — Generate phantom attractor training trajectories for the
Attractor Lab visualization in monogate explorer.

Trains an EMLTree(depth=3) to approximate π using two regularization configs:
  - λ=0.000 : 40 seeds → all converge to the ~3.1696 phantom attractor
  - λ=0.005 : 40 seeds → most converge to π

Records loss + formula value at every step, saves compact JSON to
explorer/public/attractor_data.json.

Run from python/:
    python experiments/gen_attractor_data.py

Output size: ~250–500 KB uncompressed
"""

import json
import math
import sys
import time
from pathlib import Path

import torch

# Add parent so `monogate` imports work when run from python/
sys.path.insert(0, str(Path(__file__).parent.parent))
from monogate.network import EMLTree, fit

# ── Config ────────────────────────────────────────────────────────────────────
N_SEEDS  = 40
STEPS    = 3000       # matches research_02_attractors.py (enough to see phase transition)
LR       = 5e-3       # matches research_02_attractors.py
LAMBDAS  = [0.0, 0.005]
TARGET   = math.pi
DEPTH    = 3          # 7 internal nodes, 8 leaves
LOG_STEPS = list(range(0, STEPS + 1, 20))  # record every 20 steps -> 151 points per seed

# Phantom attractor value (empirically found in research_02)
ATTRACTOR = 3.1696   # approximate; varies slightly per seed

OUT_PATH = Path(__file__).parent.parent.parent / "explorer" / "public" / "attractor_data.json"

# ── Utilities ─────────────────────────────────────────────────────────────────

def run_seed(seed: int, lam: float) -> dict:
    """Train one EMLTree seed; return trajectory dict."""
    torch.manual_seed(seed * 17 + 3)   # matches research_02_attractors.py
    model = EMLTree(depth=DEPTH)       # default init=1.0

    opt = torch.optim.Adam(model.parameters(), lr=LR)
    target_t = torch.tensor(float(TARGET))

    trajectory_loss  = []
    trajectory_value = []

    for step in range(STEPS + 1):
        if step > 0:
            opt.zero_grad()
            try:
                pred     = model()
                raw_loss = (pred - target_t) ** 2
            except (ValueError, RuntimeError):
                trajectory_loss.append(trajectory_loss[-1] if trajectory_loss else 1000.0)
                trajectory_value.append(trajectory_value[-1] if trajectory_value else 1.0)
                continue

            if not torch.isfinite(raw_loss):
                trajectory_loss.append(1000.0)
                trajectory_value.append(float("nan"))
                continue

            loss = raw_loss
            if lam > 0:
                penalty = sum((p - 1.0).abs().sum() for p in model.parameters())
                loss    = raw_loss + lam * penalty

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

        if step % 20 == 0:
            with torch.no_grad():
                try:
                    v = model().item()
                    l = ((v - TARGET) ** 2)
                except Exception:
                    v, l = float("nan"), 1000.0
            trajectory_loss.append(round(min(l, 1000.0), 6))
            trajectory_value.append(round(v, 6) if math.isfinite(v) else None)

    final_val = trajectory_value[-1]
    if final_val is not None and math.isfinite(final_val):
        dist_attractor = abs(final_val - ATTRACTOR)
        dist_pi        = abs(final_val - TARGET)
        destiny = "pi" if dist_pi < dist_attractor else "attractor"
    else:
        destiny = "diverged"

    return {
        "seed":     seed,
        "lam":      lam,
        "destiny":  destiny,
        "loss":     trajectory_loss,
        "value":    trajectory_value,
    }


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Generating attractor data: {N_SEEDS} seeds x {len(LAMBDAS)} lam values x {STEPS} steps")
    print(f"Recording every 5 steps -> {len(LOG_STEPS)} points per trajectory")
    print()

    all_runs = []
    total = N_SEEDS * len(LAMBDAS)
    done  = 0
    t0    = time.perf_counter()

    for lam in LAMBDAS:
        n_pi = 0
        n_att = 0
        n_div = 0
        for seed in range(N_SEEDS):
            run = run_seed(seed, lam)
            all_runs.append(run)
            done += 1
            if run["destiny"] == "pi":        n_pi  += 1
            elif run["destiny"] == "attractor": n_att += 1
            else:                               n_div += 1

            elapsed = time.perf_counter() - t0
            eta = elapsed / done * (total - done)
            sys.stdout.write(
                f"\r  lam={lam:.3f} seed {seed:02d}/{N_SEEDS-1}  "
                f"[pi:{n_pi} att:{n_att} div:{n_div}]  "
                f"elapsed {elapsed:.1f}s  eta {eta:.1f}s    "
            )
            sys.stdout.flush()
        print()
        print(f"  lam={lam:.3f} summary: pi={n_pi}/{N_SEEDS}  attractor={n_att}/{N_SEEDS}  diverged={n_div}/{N_SEEDS}")
        print()

    payload = {
        "meta": {
            "n_seeds":    N_SEEDS,
            "steps":      STEPS,
            "record_every": 5,
            "n_points":   len(LOG_STEPS),
            "depth":      DEPTH,
            "target":     TARGET,
            "attractor":  ATTRACTOR,
            "lambdas":    LAMBDAS,
        },
        "runs": all_runs,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Saved → {OUT_PATH}")
    print(f"File size: {size_kb:.1f} KB")
    print(f"Total time: {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
