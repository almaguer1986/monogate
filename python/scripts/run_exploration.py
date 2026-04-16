#!/usr/bin/env python3
"""
Overnight exploration run.
Generates conjectures, proves them, trains the neural scorer, logs discoveries.

Uses EMLProverV2.explore() — the real API. A single prover instance is kept
alive across all phases so the scorer accumulates experience continuously.

Usage:
    cd python
    python scripts/run_exploration.py 2>&1 | tee results/exploration_log.txt
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _proof_to_dict(proof) -> dict:
    """Convert a ProofResult to a JSON-serialisable dict."""
    return {
        "status":              proof.status,
        "confidence":          proof.confidence,
        "elapsed_s":           proof.elapsed_s,
        "node_count":          proof.node_count,
        "mcts_simulations":    proof.mcts_simulations,
        "lhs_formula":         proof.lhs_formula,
        "verification_method": proof.verification_method,
        "max_residual":        proof.max_residual,
    }


def _identity_to_dict(identity) -> dict:
    """Convert an Identity to a JSON-serialisable dict."""
    return {
        "name":       identity.name,
        "expression": identity.expression,
        "category":   identity.category,
        "difficulty": identity.difficulty,
    }


def _phase_stats(explore_result: dict, phase_time: float, name: str,
                 seed_category: str, temperature: float, n_rounds: int) -> dict:
    """Summarise one explore() result for JSON storage."""
    lc = explore_result["learning_curve"]
    total_generated = sum(r["n_conjectures"] for r in lc)
    total_proved    = sum(r["n_proved"]      for r in lc)
    total_witness   = sum(r["n_witness"]     for r in lc)
    final_buffer    = lc[-1]["scorer_buffer"] if lc else 0
    scorer_trained  = lc[-1]["scorer_trained"] if lc else False

    discoveries = []
    for identity, proof in explore_result["discovered"]:
        discoveries.append({
            "identity": _identity_to_dict(identity),
            "proof":    _proof_to_dict(proof),
        })

    return {
        "name":             name,
        "seed_category":    seed_category,
        "temperature":      temperature,
        "n_rounds":         n_rounds,
        "runtime_s":        phase_time,
        "total_generated":  total_generated,
        "total_proved":     total_proved,
        "total_witness":    total_witness,
        "prove_rate":       total_proved / max(total_generated, 1),
        "mcts_rate":        total_witness / max(total_generated, 1),
        "scorer_buffer":    final_buffer,
        "scorer_trained":   scorer_trained,
        "n_discoveries":    len(discoveries),
        "learning_curve":   lc,
        "discoveries":      discoveries,
    }


# ── Main exploration loop ─────────────────────────────────────────────────────

PHASES = [
    # (name, seed_category, temperature, n_rounds)
    ("trig_medium",    "trig",        0.7, 100),
    ("trig_high",      "trig",        0.9,  50),
    ("exp_medium",     "exponential", 0.7,  50),
    ("special_medium", "special",     0.8,  30),
    ("physics_medium", "physics",     0.7,  30),
]


def run_full_exploration() -> dict:
    from monogate.prover import EMLProverV2

    output_dir = Path("results/exploration")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")

    session: dict[str, Any] = {
        "started":        timestamp,
        "phases":         [],
        "all_discoveries": [],
        "totals":         {},
    }

    print("=" * 62)
    print("  MONOGATE OVERNIGHT EXPLORATION")
    print(f"  Started: {timestamp}")
    print("=" * 62)

    # Single prover — scorer accumulates across all phases
    prover = EMLProverV2(enable_learning=True)

    for phase_name, seed_cat, temp, n_rounds in PHASES:
        print(f"\n[{phase_name}]  seed={seed_cat}  temp={temp}  rounds={n_rounds}")
        print("-" * 50)

        t0 = time.perf_counter()
        try:
            result = prover.explore(
                n_rounds=n_rounds,
                n_per_round=20,
                seed_category=seed_cat,
                temperature=temp,
                compress_witnesses=True,
                verbose=True,
            )
        except Exception as exc:
            print(f"  [ERROR] Phase {phase_name} failed: {exc}")
            session["phases"].append({"name": phase_name, "error": str(exc)})
            continue

        phase_time = time.perf_counter() - t0
        stats = _phase_stats(result, phase_time, phase_name, seed_cat, temp, n_rounds)
        session["phases"].append(stats)
        session["all_discoveries"].extend(stats["discoveries"])

        print(
            f"\n  {phase_name} done in {phase_time:.1f}s"
            f"  generated={stats['total_generated']}"
            f"  proved={stats['total_proved']}"
            f"  witness={stats['total_witness']}"
            f"  discovered={stats['n_discoveries']}"
            f"  scorer_buf={stats['scorer_buffer']}"
        )

    # ── Aggregate totals ──────────────────────────────────────────────────────
    phases_ok = [p for p in session["phases"] if "error" not in p]
    session["totals"] = {
        "phases_completed":       len(phases_ok),
        "total_generated":        sum(p["total_generated"]  for p in phases_ok),
        "total_proved":           sum(p["total_proved"]     for p in phases_ok),
        "total_witness":          sum(p["total_witness"]    for p in phases_ok),
        "total_discoveries":      len(session["all_discoveries"]),
        "total_runtime_s":        sum(p["runtime_s"]        for p in phases_ok),
        "scorer_buffer_final":    phases_ok[-1]["scorer_buffer"]  if phases_ok else 0,
        "scorer_trained_final":   phases_ok[-1]["scorer_trained"] if phases_ok else False,
    }
    session["ended"] = datetime.now().strftime("%Y%m%d_%H%M%S")

    t = session["totals"]
    prove_rate = t["total_proved"]   / max(t["total_generated"], 1)
    mcts_rate  = t["total_witness"]  / max(t["total_generated"], 1)

    # ── Save full results ─────────────────────────────────────────────────────
    out_json = output_dir / f"exploration_{timestamp}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, default=str)

    disc_json = output_dir / f"discoveries_{timestamp}.json"
    with open(disc_json, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp":   timestamp,
            "count":       len(session["all_discoveries"]),
            "discoveries": session["all_discoveries"],
        }, f, indent=2, default=str)

    # ── Write summary markdown ────────────────────────────────────────────────
    _write_summary(session, timestamp, prove_rate, mcts_rate,
                   out_json, disc_json)

    # ── Console summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  EXPLORATION COMPLETE")
    print("=" * 62)
    runtime_min = t["total_runtime_s"] / 60
    print(f"  Total runtime       : {t['total_runtime_s']:.0f}s  ({runtime_min:.1f} min)")
    print(f"  Conjectures tested  : {t['total_generated']}")
    print(f"  Successfully proved : {t['total_proved']}  ({prove_rate:.0%})")
    print(f"  Reached MCTS tier   : {t['total_witness']}  ({mcts_rate:.1%})")
    print(f"  Novel discoveries   : {t['total_discoveries']}")
    print(f"  Scorer buffer       : {t['scorer_buffer_final']} samples")
    print(f"  Scorer trained      : {t['scorer_trained_final']}")
    print(f"\n  Full data  : {out_json}")
    print(f"  Discoveries: {disc_json}")
    print(f"  Summary    : results/exploration_summary_{timestamp}.md")

    if session["all_discoveries"]:
        print("\n  Top discoveries:")
        for i, d in enumerate(session["all_discoveries"][:15], 1):
            expr = d["identity"]["expression"]
            method = d["proof"]["status"].replace("proved_", "")
            print(f"    {i:3d}. [{method:12s}]  {expr[:60]}")

    return session


def _write_summary(session, timestamp, prove_rate, mcts_rate, out_json, disc_json):
    t = session["totals"]
    lines = [
        f"# Exploration Session Summary",
        f"",
        f"**Started:** {session['started']}  |  **Ended:** {session.get('ended', '—')}",
        f"",
        f"## Overall Results",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Phases completed | {t['phases_completed']} / {len(PHASES)} |",
        f"| Total conjectures tested | {t['total_generated']} |",
        f"| Successfully proved | {t['total_proved']} ({prove_rate:.0%}) |",
        f"| Reached MCTS tier | {t['total_witness']} ({mcts_rate:.1%}) |",
        f"| Novel discoveries | {t['total_discoveries']} |",
        f"| Scorer buffer (final) | {t['scorer_buffer_final']} samples |",
        f"| Scorer trained | {t['scorer_trained_final']} |",
        f"| Total runtime | {t['total_runtime_s']:.0f}s ({t['total_runtime_s']/60:.1f} min) |",
        f"",
        f"## Signal Interpretation",
        f"",
        f"- **Prove rate {prove_rate:.0%}**: {'Good — right difficulty balance' if 0.4 < prove_rate < 0.85 else ('Too easy — raise temperature' if prove_rate > 0.85 else 'Too hard — lower temperature')}",
        f"- **MCTS rate {mcts_rate:.1%}**: {'Training signal acquired' if mcts_rate > 0 else 'No MCTS reach — everything solved by SymPy/numerical (consider higher temperature)'}",
        f"",
        f"## Per-Phase Breakdown",
        f"",
        f"| Phase | Seed | Temp | Rounds | Generated | Proved | MCTS | Discoveries | Time |",
        f"|-------|------|------|--------|-----------|--------|------|-------------|------|",
    ]
    for p in session["phases"]:
        if "error" in p:
            lines.append(f"| {p['name']} | — | — | — | ERROR: {p['error'][:40]} | — | — | — | — |")
        else:
            lines.append(
                f"| {p['name']} | {p['seed_category']} | {p['temperature']} "
                f"| {p['n_rounds']} | {p['total_generated']} | {p['total_proved']} "
                f"| {p['total_witness']} | {p['n_discoveries']} | {p['runtime_s']:.0f}s |"
            )

    if session["all_discoveries"]:
        lines += [
            f"",
            f"## Discoveries ({len(session['all_discoveries'])} total)",
            f"",
        ]
        for i, d in enumerate(session["all_discoveries"], 1):
            expr   = d["identity"]["expression"]
            method = d["proof"]["status"].replace("proved_", "")
            nodes  = d["proof"]["node_count"]
            node_s = f"  _(nodes={nodes})_" if nodes > 0 else ""
            lines.append(f"{i}. `{expr}`  [{method}]{node_s}")
    else:
        lines += ["", "## Discoveries", "", "None found — try longer sessions or higher temperature."]

    lines += [
        f"",
        f"## Files",
        f"",
        f"- Full data: `{out_json}`",
        f"- Discoveries: `{disc_json}`",
    ]

    summary_path = Path(f"results/exploration_summary_{timestamp}.md")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run_full_exploration()
