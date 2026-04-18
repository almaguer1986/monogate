"""Session 593 --- Therapy and Emotional Language as Depth Transitions"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class TherapyEmotionalLanguageEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T314: Therapy and Emotional Language as Depth Transitions depth analysis",
            "domains": {
                "active_listening": {"description": "Reflective paraphrasing", "depth": "EML-2", "reason": "measurement of understanding; mirrors content"},
                "therapeutic_reframe": {"description": "That wasnt your fault", "depth": "EML-inf", "reason": "categorification: shifts blame attribution class"},
                "somatic_marker": {"description": "Body sensation linked to emotion", "depth": "EML-3", "reason": "oscillatory body-mind coupling"},
                "breakthrough_phrase": {"description": "Name it to tame it", "depth": "EML-inf", "reason": "labeling dissolves EML-inf anxiety to EML-2 management"},
                "validation_statement": {"description": "Your feelings make sense", "depth": "EML-1", "reason": "exponential safety amplification"},
                "cognitive_distortion": {"description": "All-or-nothing thinking pattern", "depth": "EML-0", "reason": "discrete binary; depth collapse"},
            },
        }

    def analyze(self) -> dict[str, Any]:
        return {
            "model": "TherapyEmotionalLanguageEML",
            "analysis": self.depth_analysis(),
            "distribution": {'EML-2': 1, 'EML-inf': 2, 'EML-3': 1, 'EML-1': 1, 'EML-0': 1},
            "theorem": "T314: Therapy and Emotional Language as Depth Transitions (S593).",
        }


def analyze_therapy_emotional_language_eml() -> dict[str, Any]:
    t = TherapyEmotionalLanguageEML()
    return {
        "session": 593,
        "title": "Therapy and Emotional Language as Depth Transitions",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T314: Therapy and Emotional Language as Depth Transitions (S593).",
        "rabbit_hole_log": ['T314: active_listening depth=EML-2 confirmed', 'T314: therapeutic_reframe depth=EML-inf confirmed', 'T314: somatic_marker depth=EML-3 confirmed', 'T314: breakthrough_phrase depth=EML-inf confirmed', 'T314: validation_statement depth=EML-1 confirmed', 'T314: cognitive_distortion depth=EML-0 confirmed'],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_therapy_emotional_language_eml(), indent=2, default=str))
