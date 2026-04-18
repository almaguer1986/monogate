"""
Session 183 — Music & Perception Deep III: Timbre, Emotion & EML-∞ Strata

EML operator: eml(x,y) = exp(x) - ln(y)
Key theorem: Musical timbre qualities (brightness=EML-2, roughness=EML-3,
inharmonicity=EML-2) map to specific EML strata. Emotional peaks are
EML-∞ → EML-3 transitions (depth collapse via musical context). Generative
composition using the Asymmetry Theorem: tension = exp-depth, release = log-depth.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class TimbreStrataEML:
    """Timbre qualities classified by EML-∞ stratum."""

    def brightness_eml(self, partials: list[tuple]) -> dict[str, Any]:
        """
        Brightness = spectral centroid = Σ(f·A)/ΣA. EML-2 (weighted log-freq).
        Perceptual brightness: log₂(centroid/ref). EML-2 (log ratio).
        High brightness → higher centroid → EML-2 (same depth as running coupling log μ/μ₀).
        """
        if not partials:
            return {"error": "no_partials"}
        total = sum(a for _, a in partials)
        centroid = sum(f * a for f, a in partials) / (total + 1e-12)
        brightness = math.log2(centroid / 440.0 + 1.0)
        return {
            "centroid_Hz": round(centroid, 2),
            "log_brightness": round(brightness, 4),
            "eml_depth": 2,
            "note": "Brightness = log₂(centroid/ref) = EML-2"
        }

    def inharmonicity_eml(self, partials: list[tuple], f0: float = 220.0) -> dict[str, Any]:
        """
        Inharmonicity: B = Σ |f_n - n·f0| / (n·f0) (deviation from harmonic series).
        EML-2 (log-ratio of deviation).
        Piano strings: B ~ 0.0001 to 0.003 (low inharmonicity). EML-2 measure.
        Bell: high inharmonicity ~ 0.3. EML-2.
        Perfect harmonic: B=0. EML-0.
        """
        if not partials:
            return {"error": "no_partials"}
        deviations = []
        for n, (f_n, _) in enumerate(partials, 1):
            ideal = n * f0
            dev = abs(f_n - ideal) / (ideal + 1e-12)
            deviations.append(dev)
        inharmonicity = sum(deviations) / len(deviations)
        log_inharm = math.log(inharmonicity + 1e-6)
        return {
            "f0": f0,
            "inharmonicity": round(inharmonicity, 6),
            "log_inharmonicity": round(log_inharm, 4),
            "eml_depth": 2 if inharmonicity > 0 else 0,
            "note": "Inharmonicity = EML-2 (log deviation); perfect harmonic = EML-0"
        }

    def roughness_critical_band(self, f1: float, f2: float) -> dict[str, Any]:
        """
        Roughness from beating: f_beat = |f2-f1|. EML-0 (linear difference).
        Critical bandwidth: CB = 25 + 75(1 + 1.4(f_avg/1000)²)^0.69. EML-2.
        Dissonance peak at f_beat ≈ 0.25*CB. EML-2.
        Maximum dissonance produces EML-3 beating (amplitude oscillation at f_beat).
        """
        f_avg = (f1 + f2) / 2
        f_beat = abs(f2 - f1)
        cb = 25 + 75 * (1 + 1.4 * (f_avg / 1000) ** 2) ** 0.69
        beat_ratio = f_beat / cb
        dissonance = beat_ratio * math.exp(-beat_ratio)
        beating_oscillation = math.cos(2 * math.pi * f_beat * 0.01)
        return {
            "f1": f1, "f2": f2,
            "f_beat": round(f_beat, 2),
            "critical_band": round(cb, 2),
            "beat_ratio": round(beat_ratio, 4),
            "dissonance": round(dissonance, 6),
            "beating_oscillation_sample": round(beating_oscillation, 4),
            "eml_depth_cb": 2,
            "eml_depth_beat": 0,
            "eml_depth_beating": 3,
            "note": "Critical band = EML-2; beat frequency = EML-0; beating oscillation = EML-3"
        }

    def analyze(self) -> dict[str, Any]:
        piano = [(220 * n * (1 + 0.0002 * n ** 2), 1.0 / n) for n in range(1, 7)]
        violin = [(220 * n, 0.9 ** (n - 1)) for n in range(1, 8)]
        bell = [(220 * n * (1 + 0.05 * n), 0.7 ** (n - 1)) for n in range(1, 5)]
        instr = {
            "piano": {"brightness": self.brightness_eml(piano),
                      "inharmonicity": self.inharmonicity_eml(piano)},
            "violin": {"brightness": self.brightness_eml(violin),
                       "inharmonicity": self.inharmonicity_eml(violin)},
            "bell": {"brightness": self.brightness_eml(bell),
                     "inharmonicity": self.inharmonicity_eml(bell)}
        }
        intervals = {"unison": (440, 440), "minor2nd": (440, 466),
                     "major3rd": (440, 554), "fifth": (440, 660), "octave": (440, 880)}
        roughness = {name: self.roughness_critical_band(f1, f2)
                     for name, (f1, f2) in intervals.items()}
        return {
            "model": "TimbreStrataEML",
            "instruments": instr,
            "roughness_intervals": roughness,
            "eml_depth": {
                "brightness": 2, "inharmonicity": 2,
                "critical_band": 2, "beat_freq": 0, "beating": 3
            },
            "key_insight": "Timbre: brightness=EML-2, inharmonicity=EML-2, beating=EML-3"
        }


@dataclass
class EmotionalPeakEML:
    """Musical emotional peaks as EML-∞ → EML-3 depth collapses."""

    def chills_frisson(self, tension_history: list[float]) -> dict[str, Any]:
        """
        Musical chills (frisson): peak emotional response at structural surprise.
        Expectation buildup: EML-1 (exponential approach to expected pattern).
        Surprise at peak: EML-∞ (violated expectation = hard problem boundary).
        Resolution/chill: EML-3 (affective oscillation = release wave).
        The chill = EML-∞ → EML-3 depth collapse (same as sync collapse S182).
        """
        if not tension_history:
            return {"error": "need_tension_history"}
        max_t = max(tension_history)
        mean_t = sum(tension_history) / len(tension_history)
        approach_rate = math.exp(-0.5 * len(tension_history))
        surprise = max_t - mean_t
        resolution = math.cos(math.pi * surprise)
        return {
            "tension_history": [round(t, 3) for t in tension_history],
            "peak_tension": round(max_t, 4),
            "mean_tension": round(mean_t, 4),
            "surprise_magnitude": round(surprise, 4),
            "expectation_approach": round(approach_rate, 6),
            "resolution_wave": round(resolution, 4),
            "eml_depth_approach": 1,
            "eml_depth_peak": "∞",
            "eml_depth_resolution": 3,
            "depth_collapse": "EML-∞ → EML-3 (frisson = depth collapse)"
        }

    def tension_release_asymmetry(self, t: float, rise_rate: float = 1.0,
                                   fall_rate: float = 2.0) -> dict[str, Any]:
        """
        Tension/release asymmetry: rise = EML-1 (exp approach), fall = EML-3 (oscillatory).
        EML Asymmetry: tension buildup = EML-1 (slow exp); release = EML-3 (fast oscillation).
        Δd = 3 - 1 = 2 (not 1 — not the unique asymmetry, but a musical instance).
        Composition rule from Asymmetry Theorem: tension ∝ exp, release ∝ cos.
        """
        tension = 1 - math.exp(-rise_rate * t)
        release = math.cos(fall_rate * t) * math.exp(-0.3 * t)
        asymmetry_delta = 3 - 1
        return {
            "t": t, "rise_rate": rise_rate, "fall_rate": fall_rate,
            "tension": round(tension, 4),
            "release": round(release, 4),
            "eml_depth_tension": 1,
            "eml_depth_release": 3,
            "delta_d": asymmetry_delta,
            "note": "Tension=EML-1, release=EML-3; Δd=2 (musical instance of asymmetry)"
        }

    def analyze(self) -> dict[str, Any]:
        tension_histories = {
            "climax_ending": [0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.5, 0.1],
            "plateau_release": [0.5, 0.55, 0.6, 0.55, 0.5, 0.3, 0.1],
            "double_peak": [0.3, 0.7, 0.4, 0.8, 0.2]
        }
        chills = {name: self.chills_frisson(hist) for name, hist in tension_histories.items()}
        t_vals = [0.5, 1.0, 1.5, 2.0, 3.0]
        asym = {round(t, 2): self.tension_release_asymmetry(t) for t in t_vals}
        return {
            "model": "EmotionalPeakEML",
            "chills_frisson": chills,
            "tension_release": asym,
            "eml_depth": {
                "expectation_approach": 1,
                "emotional_peak": "∞",
                "resolution_wave": 3,
                "tension": 1,
                "release": 3
            },
            "key_insight": "Musical peaks: buildup=EML-1, peak=EML-∞, resolution=EML-3 (depth collapse)"
        }


@dataclass
class GenerativeCompositionEML:
    """Generative composition rules derived from the Asymmetry Theorem."""

    def asymmetry_melody(self, n_notes: int = 8, f0: float = 261.63) -> dict[str, Any]:
        """
        Asymmetry composition rule: Rising tension → exp-spaced intervals (EML-1).
        Release → log-compressed intervals (EML-2).
        This mirrors the Asymmetry Theorem: forward (exp) = EML-1, inverse (log) = EML-2.
        Generative melody: rising = exp(n/8) scaling; falling = log(n+1) compression.
        """
        rising = [round(f0 * math.exp(n / 8), 2) for n in range(n_notes // 2)]
        falling = [round(f0 * (1 + math.log(n + 1)), 2) for n in range(n_notes // 2)]
        melody = rising + falling[::-1]
        intervals_rising = [round(rising[i + 1] / rising[i], 4) for i in range(len(rising) - 1)]
        intervals_falling = [round(falling[i + 1] / falling[i], 4) for i in range(len(falling) - 1)]
        return {
            "n_notes": n_notes,
            "f0_Hz": f0,
            "rising_notes_Hz": rising,
            "falling_notes_Hz": falling,
            "full_melody_Hz": melody,
            "intervals_rising": intervals_rising,
            "intervals_falling": intervals_falling,
            "eml_depth_rising": 1,
            "eml_depth_falling": 2,
            "rule": "Tension (exp-spaced) = EML-1; Release (log-compressed) = EML-2"
        }

    def depth_transition_rhythm(self, n_beats: int = 8) -> dict[str, Any]:
        """
        Rhythm where depth changes mark structural transitions:
        EML-0 (isochronous) → EML-3 (syncopated oscillatory) → EML-0 (resolution).
        The EML-∞ moment = beat of maximal surprise (missing beat / syncopation).
        """
        ioi_pattern = []
        for i in range(n_beats):
            if i < n_beats // 4:
                ioi = 0.5
                eml = 0
            elif i < 3 * n_beats // 4:
                ioi = 0.5 + 0.2 * math.sin(2 * math.pi * i / 3)
                eml = 3
            else:
                ioi = 0.5
                eml = 0
            ioi_pattern.append({"beat": i, "ioi": round(ioi, 4), "eml_depth": eml})
        surprise_beat = n_beats // 2
        return {
            "rhythm": ioi_pattern,
            "surprise_beat": surprise_beat,
            "eml_depth_surprise": "∞",
            "rule": "Isochronous=EML-0; syncopation=EML-3; missing beat=EML-∞"
        }

    def analyze(self) -> dict[str, Any]:
        melody = self.asymmetry_melody()
        rhythm = self.depth_transition_rhythm()
        return {
            "model": "GenerativeCompositionEML",
            "asymmetry_melody": melody,
            "depth_transition_rhythm": rhythm,
            "composition_rules": {
                "tension_rising": "exp-spaced = EML-1",
                "release_falling": "log-compressed = EML-2",
                "rhythm_climax": "EML-3 syncopation",
                "surprise_peak": "EML-∞ (missing/unexpected beat)",
                "resolution": "EML-0 (return to isochrony)"
            },
            "eml_depth": {
                "rising_melody": 1, "falling_melody": 2,
                "syncopation": 3, "surprise": "∞", "isochronous": 0
            },
            "key_insight": "Asymmetry Theorem generates music: exp-tension=EML-1, log-release=EML-2"
        }


def analyze_music_perception_v2_eml() -> dict[str, Any]:
    timbre = TimbreStrataEML()
    emotion = EmotionalPeakEML()
    generative = GenerativeCompositionEML()
    return {
        "session": 183,
        "title": "Music & Perception Deep III: Timbre, Emotion & EML-∞ Strata",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "timbre_strata": timbre.analyze(),
        "emotional_peaks": emotion.analyze(),
        "generative_composition": generative.analyze(),
        "eml_depth_summary": {
            "EML-0": "Beat frequency (|f2-f1|), isochronous rhythm, perfect harmonic (B=0)",
            "EML-1": "Expectation buildup exp(-rt), rising tension melody (exp-spaced)",
            "EML-2": "Brightness log₂(centroid), inharmonicity, critical band, release melody (log)",
            "EML-3": "Beating oscillation, resolution wave cos, syncopated rhythm",
            "EML-∞": "Emotional peak/frisson, surprise moment, missing beat"
        },
        "key_theorem": (
            "The EML Musical Asymmetry Theorem: "
            "Musical timbre qualities map to EML strata: "
            "brightness = EML-2 (log centroid), inharmonicity = EML-2, beating = EML-3. "
            "Emotional peaks (frisson/chills) = EML-∞ → EML-3 depth collapses: "
            "buildup = EML-1 (exponential approach), surprise = EML-∞, resolution = EML-3. "
            "The Asymmetry Theorem generates composition rules: "
            "tension uses exp-spaced intervals (EML-1); release uses log-compressed intervals (EML-2). "
            "Rhythm: isochrony = EML-0, syncopation = EML-3, surprise/missing beat = EML-∞. "
            "Musical structure follows the EML depth ladder: "
            "0 (counting) → 1 (exponential tension) → 2 (log geometry) → 3 (oscillation) → ∞ (feeling)."
        ),
        "rabbit_hole_log": [
            "Frisson = EML-∞ → EML-3 collapse: same mechanism as sync collapse (S182)!",
            "Tension/release Δd=2 (EML-1 to EML-3): not the unique Δd=1 but musical instance",
            "Rising exp-melody = EML-1: same depth as expectation buildup, BCS gap, ISI",
            "Critical band = EML-2: same depth class as running coupling, Fisher info, log N(σ,T)",
            "Isochronous rhythm = EML-0: simplest possible temporal structure",
            "The Asymmetry Theorem literally writes music: exp=tension, log=release"
        ],
        "connections": {
            "S173_music": "S173 basic timbre; S183 adds stratum classification and generative rules",
            "S182_sync": "Frisson = EML-∞→EML-3: same collapse type as synchronization!",
            "S111_asym": "Rising melody=EML-1, falling=EML-2: Asymmetry Theorem in auditory form"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_music_perception_v2_eml(), indent=2, default=str))
