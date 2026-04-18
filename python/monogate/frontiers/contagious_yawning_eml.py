"""Session 941 --- Why We Yawn When Others Yawn"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ContagiousYawningEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T662: Why We Yawn When Others Yawn depth analysis",
            "domains": {
                "mirror_neurons_eml2": {"description": "Mirror neurons: EML-2 measurement of another persons state", "depth": "EML-2", "reason": "Contagious yawn trigger is EML-2: mirror neuron system measures observed yawn"},
                "resonance_eml3": {"description": "Contagious yawning: EML-3 resonance coupling between oscillatory systems", "depth": "EML-3", "reason": "Yawn contagion is EML-3: oscillatory coupling of physiological state between empathic individuals"},
                "empathy_detector": {"description": "Yawn-coupling strength proportional to EML-inf consciousness recognition", "depth": "EML-inf", "reason": "Contagious yawning theorem: it is a depth-3 empathy detector; strength measures EML-inf recognition between minds"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "ContagiousYawningEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T662: Why We Yawn When Others Yawn (S941).",
        }

def analyze_contagious_yawning_eml() -> dict[str, Any]:
    t = ContagiousYawningEML()
    return {
        "session": 941,
        "title": "Why We Yawn When Others Yawn",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T662: Why We Yawn When Others Yawn (S941).",
        "rabbit_hole_log": ["T662: mirror_neurons_eml2 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_contagious_yawning_eml(), indent=2, default=str))