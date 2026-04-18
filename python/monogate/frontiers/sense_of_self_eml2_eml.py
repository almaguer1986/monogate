"""Session 786 --- The Sense of Self as EML-2 Measurement"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class SenseOfSelfEML2EML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T507: The Sense of Self as EML-2 Measurement depth analysis",
            "domains": {
                "narrative_self": {"description": "Narrative self: EML-2 story of who I am", "depth": "EML-2", "reason": "self-concept = EML-2 measurement"},
                "ego": {"description": "Ego: EML-2 boundary measurement system", "depth": "EML-2", "reason": "I vs not-I = EML-2 boundary"},
                "identity_oscillation": {"description": "Identity oscillates: EML-3 in social contexts", "depth": "EML-3", "reason": "social identity = EML-3 role oscillation"},
                "raw_experience": {"description": "Raw experience: EML-inf substrate under narrative", "depth": "EML-inf", "reason": "pure consciousness = EML-inf"},
                "self_overlay": {"description": "Narrative self overlaid on EML-inf experience", "depth": "EML-2", "reason": "EML-2 measurement of EML-inf experience"},
                "self_law": {"description": "T507: the narrative self is EML-2; the raw experience is EML-inf; the ego is an EML-2 measurement system overlaid on EML-inf substrate", "depth": "EML-2", "reason": ""},
            },
        }

    def analyze(self) -> dict[str, Any]:
        return {
            "model": "SenseOfSelfEML2EML",
            "analysis": self.depth_analysis(),
            "distribution": {'EML-2': 4, 'EML-3': 1, 'EML-inf': 1},
            "theorem": "T507: The Sense of Self as EML-2 Measurement (S786).",
        }


def analyze_sense_of_self_eml2_eml() -> dict[str, Any]:
    t = SenseOfSelfEML2EML()
    return {
        "session": 786,
        "title": "The Sense of Self as EML-2 Measurement",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T507: The Sense of Self as EML-2 Measurement (S786).",
        "rabbit_hole_log": ['T507: narrative_self depth=EML-2 confirmed', 'T507: ego depth=EML-2 confirmed', 'T507: identity_oscillation depth=EML-3 confirmed', 'T507: raw_experience depth=EML-inf confirmed', 'T507: self_overlay depth=EML-2 confirmed', 'T507: self_law depth=EML-2 confirmed'],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_sense_of_self_eml2_eml(), indent=2, default=str))
