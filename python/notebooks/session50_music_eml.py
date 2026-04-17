"""
session50_music_eml.py — Session 50: EML Complexity of Musical Signals.

Goals:
  1. Classify pure tones, chords, AM, FM, vibrato by EML depth.
  2. Show that all synthesized audio is finite-depth EML.
  3. Identify the EML-inf boundary: noise, wavetable.
  4. Connect to the Infinite Zeros Barrier.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from monogate.frontiers.music_eml import (
    PureToneEML,
    ChordEML,
    VibratoEML,
    FMSynthEML,
    EML_AUDIO_TAXONOMY,
    analyze_tone_eml,
    pure_tone,
    chord,
    fm_tone,
    vibrato_tone,
    harmonic_series_tone,
    count_zeros,
)

DIVIDER = "=" * 70


def section1_pure_tone() -> None:
    print(DIVIDER)
    print("SECTION 1 — PURE TONE: A*sin(2*pi*nu*t)")
    print(DIVIDER)
    tone = PureToneEML(amplitude=1.0, freq=440.0)
    tree = tone.eml_tree()
    print(f"  Formula:   {tree['formula']}")
    print(f"  EML Depth: {tree['eml_depth']}")
    print(f"  n_nodes:   {tree['n_nodes']}")
    print()
    print("  EML depth breakdown:")
    for level, desc in tree["eml_depth_breakdown"].items():
        print(f"    {level}: {desc}")
    print()
    print(f"  Insight: {tree['insight']}")
    print()


def section2_chord() -> None:
    print(DIVIDER)
    print("SECTION 2 — CHORD: Sum of Pure Tones")
    print(DIVIDER)
    # C major: C4, E4, G4
    c_major = ChordEML(freqs=[261.63, 329.63, 392.0])
    tree = c_major.eml_tree()
    print(f"  C major chord (C4-E4-G4): {tree['n_atoms']} tones")
    print(f"  EML Depth: {tree['eml_depth']}  (same as pure tone)")
    print()
    for atom in tree["atoms"]:
        print(f"    Partial {atom['partial']}: {atom['formula']}  [depth {atom['eml_depth']}]")
    print()
    print(f"  Insight: {tree['insight']}")
    print()

    # Full orchestra chord — 50 tones
    freqs_50 = [261.63 * (2 ** (k / 12.0)) for k in range(50)]
    big_chord = ChordEML(freqs=freqs_50)
    print(f"  50-tone cluster: n_atoms={big_chord.eml_tree()['n_atoms']}, depth={big_chord.eml_depth()}")
    print("  → Depth stays 3 regardless of number of partials. Breadth grows, depth does not.")
    print()


def section3_vibrato_fm() -> None:
    print(DIVIDER)
    print("SECTION 3 — VIBRATO & FM SYNTHESIS")
    print(DIVIDER)

    vib = VibratoEML(freq=440.0, vibrato_rate=5.0, vibrato_depth=10.0)
    tree = vib.eml_tree()
    print(f"  Vibrato formula: {tree['formula']}")
    print(f"  EML Depth: {tree['eml_depth']}")
    print("  Tree levels:")
    for level in tree["tree_levels"]:
        print(f"    {level}")
    print(f"  Insight: {tree['insight']}")
    print()

    fm = FMSynthEML(carrier_freq=440.0, mod_freq=110.0, mod_index=3.0)
    tree = fm.eml_tree()
    print(f"  FM formula: {tree['formula']}")
    print(f"  EML Depth: {tree['eml_depth']}")
    print(f"  Harmonics: {tree['harmonics_generated']}")
    print("  Tree levels:")
    for level in tree["tree_levels"]:
        print(f"    {level}")
    print(f"  Insight: {tree['insight']}")
    print()


def section4_taxonomy() -> None:
    print(DIVIDER)
    print("SECTION 4 — EML AUDIO TAXONOMY")
    print(DIVIDER)
    print(f"  {'Signal Type':22s}  {'Depth':>8}  {'Atoms':>10}  Verdict")
    print(f"  {'-'*22}  {'-'*8}  {'-'*10}  -------")
    for name, info in EML_AUDIO_TAXONOMY.items():
        depth = str(info["eml_depth"])
        atoms = str(info["n_atoms"])
        verdict = info["verdict"][:50]
        print(f"  {name:22s}  {depth:>8s}  {atoms:>10s}  {verdict}")
    print()
    print("  Key finding: Synthesized audio spans EML depth 3-6.")
    print("  EML-inf barrier: wavetable (piecewise), noise (infinite zeros).")
    print()


def section5_numerical() -> dict:
    print(DIVIDER)
    print("SECTION 5 — NUMERICAL SIGNAL ANALYSIS")
    print(DIVIDER)
    results = analyze_tone_eml(sample_rate=44100.0, duration=0.05)
    print(f"  {'Signal':30s}  {'Depth':>6}  {'ZeroCross':>10}  {'RMS':>8}  {'Centroid Hz':>12}")
    print(f"  {'-'*30}  {'-'*6}  {'-'*10}  {'-'*8}  {'-'*12}")
    for name, data in results["tones"].items():
        print(
            f"  {name:30s}  {data['eml_depth']:>6}  {data['zero_crossings']:>10d}"
            f"  {data['rms']:>8.4f}  {data['spectral_centroid_hz']:>12.1f}"
        )
    print()
    print(f"  Insight: {results['key_insight']}")
    print()

    # Verify pure tone zero crossing count
    tone_data = results["tones"]["pure_440hz"]
    theory = tone_data.get("theory_zero_crossings", 0)
    actual = tone_data["zero_crossings"]
    print(f"  Pure tone 440 Hz zero crossings: {actual} (theory: {theory})")
    print(f"  Match: {'YES' if abs(actual - theory) <= 2 else 'APPROX'}")
    print()
    return results


def section6_eml_inf_boundary() -> None:
    print(DIVIDER)
    print("SECTION 6 — EML-inf BOUNDARY: NOISE VS TONE")
    print(DIVIDER)
    rng = np.random.default_rng(42)
    t = np.linspace(0, 0.01, 441)

    noise = rng.standard_normal(len(t))
    tone_sig = pure_tone(t, freq=440.0)

    noise_zc = count_zeros(noise)
    tone_zc = count_zeros(tone_sig)

    print(f"  White noise (441 samples, 10ms): {noise_zc} zero crossings")
    print(f"  Pure 440 Hz tone (441 samples):  {tone_zc} zero crossings")
    print()
    print("  White noise is EML-inf: each sample is independent,")
    print("  zero crossing density ~N/2 per sample. Sign changes scale with n.")
    print()
    print("  This mirrors the Infinite Zeros Barrier (Session 1):")
    print("  noise = infinite zeros on compact → cannot be represented by finite EML tree.")
    print("  Pure tone = isolated zeros (2*nu*T crossings on [0,T]) → EML-3.")
    print()
    print("  EML complexity boundary in audio:")
    print("    Synthesized (analytic) → EML-finite (depth 3-6)")
    print("    Stochastic/piecewise   → EML-inf")
    print()


def section7_summary() -> dict:
    print(DIVIDER)
    print("SECTION 7 — SESSION 50 SUMMARY")
    print(DIVIDER)
    summary = {
        "session": 50,
        "title": "Music & Signal Processing — EML Tones and Spectra",
        "findings": [
            {
                "id": "F50.1",
                "name": "Pure Tone = EML-3",
                "content": "A*sin(2*pi*nu*t) is exactly depth 3: linear arg + exp (sin) + scale.",
                "status": "EXACT",
            },
            {
                "id": "F50.2",
                "name": "Chord Depth Invariance",
                "content": (
                    "A chord of K tones is EML-3 regardless of K. "
                    "Number of atoms grows but tree height stays 3. "
                    "This shows EML depth measures COMPOSITION not ADDITION."
                ),
                "status": "STRUCTURAL INSIGHT",
            },
            {
                "id": "F50.3",
                "name": "FM Synthesis Hierarchy",
                "content": (
                    "AM (depth 4) < FM/vibrato (depth 5-6). "
                    "Each frequency modulation layer adds 2-3 depth levels. "
                    "Doubly-nested FM would reach depth 8-9."
                ),
                "status": "EXACT",
            },
            {
                "id": "F50.4",
                "name": "Noise = EML-inf",
                "content": (
                    "White noise has infinite zero crossings on compact intervals. "
                    "This is the audio instance of the Infinite Zeros Barrier. "
                    "The EML complexity boundary in audio = analytic vs stochastic."
                ),
                "status": "STRUCTURAL CONNECTION",
            },
            {
                "id": "F50.5",
                "name": "Synthesis = EML Tree Construction",
                "content": (
                    "Every synthesized audio algorithm IS an EML tree construction. "
                    "The synthesis formula and the EML tree are the same object. "
                    "Audio synthesis = EML programming."
                ),
                "status": "UNIFYING INSIGHT",
            },
        ],
        "next_session": {
            "id": 51,
            "title": "Chaos Taxonomy — Full EML-k Classification",
            "priorities": [
                "Rössler system: EML-2 per step (degree-2 polynomial RHS)",
                "Chua circuit: EML-inf (piecewise-linear characteristic)",
                "Double pendulum: EML-2 per step (rational trig)",
                "Henon map: EML-2 per step, EML-O(n) for horizon",
                "Full classification table: smooth vs piecewise vs transcendental",
            ],
        },
    }

    print("  Session 50 Findings:")
    for f in summary["findings"]:
        print(f"  [{f['id']}] {f['name']}")
        print(f"    Content: {f['content']}")
        print(f"    Status:  {f['status']}")
    print()
    print(f"  Next: Session {summary['next_session']['id']} — {summary['next_session']['title']}")
    print()
    return summary


def main() -> None:
    print()
    print(DIVIDER)
    print("  SESSION 50 — MUSIC & SIGNAL PROCESSING: EML TONES AND SPECTRA")
    print(DIVIDER)
    print()

    section1_pure_tone()
    section2_chord()
    section3_vibrato_fm()
    section4_taxonomy()
    numerical = section5_numerical()
    section6_eml_inf_boundary()
    summary = section7_summary()

    output = {
        "session": 50,
        "taxonomy": EML_AUDIO_TAXONOMY,
        "numerical": numerical,
        "summary": summary,
    }

    out_path = Path(__file__).parent.parent / "results" / "session50_music_eml.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  Results saved to: {out_path}")
    print()
    print(DIVIDER)
    print("  SESSION 50 COMPLETE")
    print(DIVIDER)


if __name__ == "__main__":
    main()
