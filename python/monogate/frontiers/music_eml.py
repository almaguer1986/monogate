"""
music_eml.py — EML Complexity for Musical Signals.

Session 50 findings:
  - Pure tone A*sin(2*pi*nu*t): depth-3 EML (cos via exp, linear arg)
  - Vibrato A*sin(2*pi*(nu + delta*sin(2*pi*fm*t))*t): depth 5-6 EML
  - Chord = sum of tones: EML-3 linear combination, one atom per partial
  - AM synthesis: depth 4 (product of two EML-3 signals)
  - FM synthesis: depth 5 (composed frequency modulation)
  - Piano tone (harmonic series): EML-3 in infinite basis, EML-k per truncation

Key insight: ALL synthesized audio is finite-depth EML.
  The EML tree for a sound IS the synthesis formula.
  Audio synthesis = EML tree construction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

__all__ = [
    "pure_tone",
    "vibrato_tone",
    "chord",
    "am_tone",
    "fm_tone",
    "harmonic_series_tone",
    "PureToneEML",
    "ChordEML",
    "VibratoEML",
    "FMSynthEML",
    "EML_AUDIO_TAXONOMY",
    "analyze_tone_eml",
]


# ── Waveform Generators ───────────────────────────────────────────────────────

def pure_tone(
    t: np.ndarray,
    amplitude: float = 1.0,
    freq: float = 440.0,
    phase: float = 0.0,
) -> np.ndarray:
    """f(t) = A * sin(2*pi*nu*t + phi). EML depth 3."""
    return amplitude * np.sin(2.0 * math.pi * freq * t + phase)


def vibrato_tone(
    t: np.ndarray,
    amplitude: float = 1.0,
    freq: float = 440.0,
    vibrato_rate: float = 5.0,
    vibrato_depth: float = 10.0,
    phase: float = 0.0,
) -> np.ndarray:
    """f(t) = A * sin(2*pi*(nu + delta*sin(2*pi*fm*t))*t + phi). EML depth 6."""
    inst_freq = freq + vibrato_depth * np.sin(2.0 * math.pi * vibrato_rate * t)
    return amplitude * np.sin(2.0 * math.pi * inst_freq * t + phase)


def chord(
    t: np.ndarray,
    freqs: list[float],
    amplitudes: list[float] | None = None,
) -> np.ndarray:
    """Sum of pure tones. EML-3 linear combination."""
    if amplitudes is None:
        amplitudes = [1.0 / len(freqs)] * len(freqs)
    return sum(a * np.sin(2.0 * math.pi * f * t) for a, f in zip(amplitudes, freqs))


def am_tone(
    t: np.ndarray,
    carrier_freq: float = 440.0,
    mod_freq: float = 3.0,
    mod_depth: float = 0.5,
) -> np.ndarray:
    """AM: f(t) = (1 + m*cos(2*pi*fm*t)) * sin(2*pi*fc*t). EML depth 4."""
    envelope = 1.0 + mod_depth * np.cos(2.0 * math.pi * mod_freq * t)
    carrier = np.sin(2.0 * math.pi * carrier_freq * t)
    return envelope * carrier


def fm_tone(
    t: np.ndarray,
    carrier_freq: float = 440.0,
    mod_freq: float = 110.0,
    mod_index: float = 3.0,
) -> np.ndarray:
    """FM synthesis: f(t) = sin(2*pi*fc*t + beta*sin(2*pi*fm*t)). EML depth 5."""
    phase_mod = mod_index * np.sin(2.0 * math.pi * mod_freq * t)
    return np.sin(2.0 * math.pi * carrier_freq * t + phase_mod)


def harmonic_series_tone(
    t: np.ndarray,
    fundamental: float = 261.63,
    n_harmonics: int = 8,
    decay: float = 0.6,
) -> np.ndarray:
    """Piano-like tone: f(t) = sum_{k=1}^{K} decay^{k-1} * sin(2*pi*k*f0*t).

    EML structure: K atoms each at depth 3; linear combination.
    Each harmonic = one EML-3 atom. Total: EML-3 in K-atom basis.
    """
    signal = np.zeros_like(t)
    for k in range(1, n_harmonics + 1):
        signal += (decay ** (k - 1)) * np.sin(2.0 * math.pi * k * fundamental * t)
    return signal


# ── EML Analysis Classes ──────────────────────────────────────────────────────

@dataclass
class PureToneEML:
    """EML tree analysis for a pure sinusoidal tone."""
    amplitude: float = 1.0
    freq: float = 440.0
    phase: float = 0.0

    def eml_tree(self) -> dict[str, object]:
        return {
            "formula": f"f(t) = {self.amplitude} * sin(2*pi*{self.freq}*t + {self.phase})",
            "eml_depth": 3,
            "tree": {
                "root": "scalar_multiply",
                "left": self.amplitude,
                "right": {
                    "op": "sin",
                    "arg": {
                        "op": "add",
                        "left": {
                            "op": "scalar_multiply",
                            "left": 2.0 * math.pi * self.freq,
                            "right": "t",
                        },
                        "right": self.phase,
                    },
                },
            },
            "eml_depth_breakdown": {
                "depth_1": "exp(-s*ln(n)) — the Dirichlet atom for n^{-s}",
                "depth_2": "2*pi*nu*t (linear in t — EML-2 via multiply)",
                "depth_3": "sin(x) = Im(exp(ix)) — one EML application",
            },
            "n_nodes": 5,
            "insight": (
                "sin(2*pi*nu*t) = Im(exp(2*pi*i*nu*t)). "
                "The EML gate eml(ix, 1) + 1 = exp(ix) - ln(1) = exp(ix). "
                "Taking Im gives sin. Pure tone IS one EML-3 node."
            ),
        }

    def eml_depth(self) -> int:
        return 3


@dataclass
class ChordEML:
    """EML tree for a chord (sum of pure tones)."""
    freqs: list[float]
    amplitudes: list[float] | None = None

    def __post_init__(self) -> None:
        if self.amplitudes is None:
            self.amplitudes = [1.0 / len(self.freqs)] * len(self.freqs)

    def eml_tree(self) -> dict[str, object]:
        n = len(self.freqs)
        atoms = [
            {
                "partial": k + 1,
                "freq": f,
                "amplitude": a,
                "eml_depth": 3,
                "formula": f"{a:.3f} * sin(2*pi*{f}*t)",
            }
            for k, (f, a) in enumerate(zip(self.freqs, self.amplitudes))
        ]
        return {
            "formula": f"f(t) = sum of {n} pure tones",
            "freqs": self.freqs,
            "eml_depth": 3,
            "n_atoms": n,
            "atoms": atoms,
            "insight": (
                f"A {n}-note chord is a linear combination of {n} EML-3 atoms. "
                "EML depth stays at 3 regardless of chord size — "
                "depth counts the TREE HEIGHT, not the number of parallel branches. "
                "Each partial is an independent depth-3 subtree; they combine at depth 0 (sum)."
            ),
        }

    def eml_depth(self) -> int:
        return 3


@dataclass
class VibratoEML:
    """EML tree for vibrato (frequency-modulated pitch oscillation)."""
    freq: float = 440.0
    vibrato_rate: float = 5.0
    vibrato_depth: float = 10.0

    def eml_tree(self) -> dict[str, object]:
        return {
            "formula": (
                f"f(t) = sin(2*pi*({self.freq} + {self.vibrato_depth}"
                f"*sin(2*pi*{self.vibrato_rate}*t))*t)"
            ),
            "eml_depth": 6,
            "tree_levels": [
                "L1: t (input)",
                "L2: 2*pi*fm*t (linear scale)",
                "L3: sin(2*pi*fm*t) (inner vibrato oscillation — EML-3)",
                "L4: nu + delta*sin(...) (instantaneous frequency)",
                "L5: 2*pi * inst_freq * t (argument to outer sin)",
                "L6: sin(2*pi*inst_freq*t) (final output)",
            ],
            "insight": (
                "Vibrato nests two sinusoids: sin inside sin. "
                "Each sin adds 3 to the depth; sharing the input t reduces it. "
                "Net depth: 6 = 3 (outer sin) + 3 (inner frequency modulation). "
                "This matches FM synthesis with mod_index=delta/nu (small)."
            ),
        }

    def eml_depth(self) -> int:
        return 6


@dataclass
class FMSynthEML:
    """EML tree for FM synthesis: f(t) = sin(2*pi*fc*t + beta*sin(2*pi*fm*t))."""
    carrier_freq: float = 440.0
    mod_freq: float = 110.0
    mod_index: float = 3.0

    def eml_tree(self) -> dict[str, object]:
        return {
            "formula": (
                f"f(t) = sin(2*pi*{self.carrier_freq}*t "
                f"+ {self.mod_index}*sin(2*pi*{self.mod_freq}*t))"
            ),
            "eml_depth": 5,
            "tree_levels": [
                "L1: t",
                "L2: 2*pi*fm*t  AND  2*pi*fc*t (two parallel linear nodes)",
                "L3: sin(2*pi*fm*t) (modulator sine)",
                "L4: 2*pi*fc*t + beta*sin(2*pi*fm*t) (phase sum)",
                "L5: sin(phase) (carrier sine with FM phase)",
            ],
            "harmonics_generated": "Bessel function spectrum: J_k(beta) at k*fm ± fc",
            "insight": (
                f"FM synthesis with mod_index={self.mod_index} generates Bessel-function "
                "harmonic spectrum. The EML depth is 5: the phase argument composes "
                "two depth-3 branches (carrier and modulator) at depth 4, "
                "then the outer sin adds one more level."
            ),
        }

    def eml_depth(self) -> int:
        return 5


# ── Zero Count for Signal Analysis ───────────────────────────────────────────

def count_zeros(signal: np.ndarray) -> int:
    """Count sign changes (zero crossings) in a signal."""
    return int(np.sum(np.diff(np.sign(signal)) != 0))


def spectral_centroid(signal: np.ndarray, sample_rate: float = 44100.0) -> float:
    """Spectral centroid in Hz."""
    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / sample_rate)
    if np.sum(spectrum) < 1e-12:
        return 0.0
    return float(np.sum(freqs * spectrum) / np.sum(spectrum))


# ── Taxonomy ──────────────────────────────────────────────────────────────────

EML_AUDIO_TAXONOMY: dict[str, dict[str, object]] = {
    "pure_tone": {
        "formula": "A*sin(2*pi*nu*t)",
        "eml_depth": 3,
        "n_atoms": 1,
        "synthesis_type": "additive",
        "verdict": "EML-3: one atom, one EML gate (exp → sin)",
    },
    "chord": {
        "formula": "sum_k A_k*sin(2*pi*nu_k*t)",
        "eml_depth": 3,
        "n_atoms": "K (number of partials)",
        "synthesis_type": "additive",
        "verdict": "EML-3: K atoms in parallel, depth stays 3",
    },
    "vibrato": {
        "formula": "A*sin(2*pi*(nu + delta*sin(2*pi*fm*t))*t)",
        "eml_depth": 6,
        "n_atoms": 1,
        "synthesis_type": "FM (frequency modulation)",
        "verdict": "EML-6: two nested sinusoids, depth doubles",
    },
    "am_synthesis": {
        "formula": "(1 + m*cos(2*pi*fm*t)) * sin(2*pi*fc*t)",
        "eml_depth": 4,
        "n_atoms": 2,
        "synthesis_type": "AM (amplitude modulation)",
        "verdict": "EML-4: product of two EML-3 signals adds one depth level",
    },
    "fm_synthesis": {
        "formula": "sin(2*pi*fc*t + beta*sin(2*pi*fm*t))",
        "eml_depth": 5,
        "n_atoms": 1,
        "synthesis_type": "FM (phase modulation)",
        "verdict": "EML-5: phase argument composes two branches at depth 4 + outer sin",
    },
    "harmonic_series": {
        "formula": "sum_{k=1}^K decay^(k-1) * sin(2*pi*k*f0*t)",
        "eml_depth": 3,
        "n_atoms": "K",
        "synthesis_type": "additive (harmonic)",
        "verdict": "EML-3: K harmonic atoms, same depth as pure tone — only breadth grows",
    },
    "wavetable": {
        "formula": "W[phase(t)] where W is a lookup table",
        "eml_depth": "inf",
        "n_atoms": "inf",
        "synthesis_type": "wavetable",
        "verdict": "EML-inf: arbitrary wavetable is not real-analytic (piecewise interpolation)",
    },
    "noise": {
        "formula": "random process",
        "eml_depth": "inf",
        "n_atoms": "inf",
        "synthesis_type": "stochastic",
        "verdict": "EML-inf: white noise has infinitely many sign changes on every interval",
    },
}


def analyze_tone_eml(
    sample_rate: float = 44100.0,
    duration: float = 0.05,
) -> dict[str, object]:
    """Run all tone generators and report EML depths + signal properties."""
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)

    results = {}

    # Pure tone A4 = 440 Hz
    sig = pure_tone(t, freq=440.0)
    results["pure_440hz"] = {
        "eml_depth": 3,
        "n_samples": len(t),
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
        "theory_zero_crossings": int(440.0 * duration * 2),
    }

    # Major chord C4-E4-G4
    sig = chord(t, freqs=[261.63, 329.63, 392.0])
    results["major_chord_CEG"] = {
        "eml_depth": 3,
        "n_atoms": 3,
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
    }

    # Vibrato
    sig = vibrato_tone(t, freq=440.0, vibrato_rate=5.0, vibrato_depth=10.0)
    results["vibrato_440hz"] = {
        "eml_depth": 6,
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
    }

    # AM synthesis
    sig = am_tone(t, carrier_freq=440.0, mod_freq=3.0, mod_depth=0.5)
    results["am_440hz"] = {
        "eml_depth": 4,
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
    }

    # FM synthesis
    sig = fm_tone(t, carrier_freq=440.0, mod_freq=110.0, mod_index=3.0)
    results["fm_440hz_beta3"] = {
        "eml_depth": 5,
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
    }

    # Harmonic series (piano-like)
    sig = harmonic_series_tone(t, fundamental=261.63, n_harmonics=8)
    results["harmonic_piano_C4"] = {
        "eml_depth": 3,
        "n_atoms": 8,
        "zero_crossings": count_zeros(sig),
        "rms": float(np.sqrt(np.mean(sig**2))),
        "spectral_centroid_hz": spectral_centroid(sig, sample_rate),
    }

    return {
        "sample_rate": sample_rate,
        "duration_s": duration,
        "n_samples": len(t),
        "tones": results,
        "taxonomy": EML_AUDIO_TAXONOMY,
        "key_insight": (
            "ALL standard synthesized audio is finite-depth EML. "
            "The EML tree for a sound IS its synthesis formula. "
            "Depth hierarchy: pure tone (3) < AM (4) < FM (5) < vibrato (6). "
            "Chord/harmonic series stay at depth 3 regardless of how many partials — "
            "depth = tree height, not number of atoms. "
            "Only non-analytic signals (wavetable, noise) are EML-inf."
        ),
    }
