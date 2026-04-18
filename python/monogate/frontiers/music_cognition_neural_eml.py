"""Session 494 — Music Cognition & Neural Correlates of Harmony"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class MusicCognitionNeuralEML:

    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T215: EML depth analysis of music cognition",
            "domains": {
                "pitch_frequencies": {
                    "description": "Frequency ratios: octave=2:1, fifth=3:2, etc.",
                    "depth": "EML-0",
                    "reason": "Simple integer ratios — discrete counting"
                },
                "equal_temperament": {
                    "description": "f_n = f₀·2^{n/12} — equal-tempered scale",
                    "depth": "EML-2",
                    "reason": "2^{n/12} = exp((n/12)ln2) — algebraic root (depth-2 algebraic number)"
                },
                "sound_wave": {
                    "description": "Pure tone: A·sin(2πft + φ)",
                    "depth": "EML-3",
                    "reason": "Sinusoidal = explicit EML-3 oscillation"
                },
                "harmonic_series": {
                    "description": "Overtones: f, 2f, 3f, 4f, ... — Fourier decomposition",
                    "depth": "EML-3",
                    "reason": "Σ aₙ sin(2πnft) — sum of EML-3 oscillations = EML-3"
                },
                "dissonance": {
                    "description": "Roughness from beating: |f₁-f₂| ~ interference",
                    "depth": "EML-3",
                    "reason": "Amplitude modulation: cos((f₁-f₂)t)·cos((f₁+f₂)t) — product of oscillations"
                },
                "emotional_response": {
                    "description": "Chills, tension, release — neurological response to music",
                    "depth": "EML-∞",
                    "reason": "Subjective experience of music — the qualia Horizon"
                },
                "musical_expectation": {
                    "description": "IDYOM model: information content of melodic events",
                    "depth": "EML-2",
                    "reason": "Surprisal = -log P(note|context) — information-theoretic (EML-2)"
                },
                "key_modulation": {
                    "description": "Modulation between musical keys",
                    "depth": "EML-3",
                    "reason": "Key = equivalence class of EML-3 oscillation modes; modulation = phase shift"
                }
            },
            "circle_of_fifths_revelation": (
                "Is the circle of fifths a depth-1 traversal? "
                "Answer: NO — it is a depth-3 structure. "
                "Each fifth = multiply by 3/2 = EML-2 ratio step. "
                "But the circle closes at 12 steps: (3/2)^12 ≈ 2^7 (Pythagorean comma). "
                "The circle = exponential oscillation of EML-3 closing on itself. "
                "Atonality (Schoenberg): removes the EML-3 tonal center → not EML-∞, but EML-3 without anchor."
            )
        }

    def analyze(self) -> dict[str, Any]:
        return {
            "model": "MusicCognitionNeuralEML",
            "analysis": self.depth_analysis(),
            "distribution": {"EML-0": 1, "EML-2": 2, "EML-3": 4, "EML-∞": 1},
            "verdict": "Music is overwhelmingly EML-3. Harmony = EML-3. Emotion = EML-∞.",
            "theorem": "T215: Music Cognition Depth — sound/harmony/keys EML-3, emotion EML-∞"
        }


def analyze_music_cognition_neural_eml() -> dict[str, Any]:
    t = MusicCognitionNeuralEML()
    return {
        "session": 494,
        "title": "Music Cognition & Neural Correlates of Harmony",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": (
            "T215: Music Cognition Depth (S494). "
            "Music IS EML-3: pure tones, harmonics, dissonance, key modulation all oscillatory. "
            "Circle of fifths: EML-3 oscillation that closes on itself (12 steps = octave). "
            "Emotion/qualia: EML-∞. "
            "Revelation: music cognition = perception of EML-3 structure by an EML-3 brain."
        ),
        "rabbit_hole_log": [
            "Pure tone sin(2πft): explicit EML-3",
            "Equal temperament 2^{n/12}: EML-2 (algebraic root)",
            "Circle of fifths: (3/2)^12 ≈ 2^7 = EML-3 cycling back",
            "Emotional response: qualia Horizon = EML-∞",
            "T215: Music = EML-3 all the way down; brain perceiving EML-3"
        ]
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_music_cognition_neural_eml(), indent=2, default=str))
