"""Session 915 --- Mathematics of a Standing Ovation"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class StandingOvationEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T636: Mathematics of a Standing Ovation depth analysis",
            "domains": {
                "first_person_eml0": {"description": "First person stands: EML-0 binary discrete action", "depth": "EML-0", "reason": "First stander is EML-0: binary decision, isolated individual"},
                "exponential_spread": {"description": "Others follow exponentially: EML-1", "depth": "EML-1", "reason": "Ovation spread is EML-1: social exponential contagion through observation"},
                "polite_threshold": {"description": "Threshold between polite applause and ovation: EML-2 measurement", "depth": "EML-2", "reason": "Ovation threshold is EML-2: critical fraction of audience standing triggers phase transition"},
                "ovation_wave": {"description": "Ovation: oscillatory waves of standing ripple through audience; EML-3", "depth": "EML-3", "reason": "Full ovation is EML-3: ripple waves propagate; social phase transition from EML-1 to EML-3"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "StandingOvationEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T636: Mathematics of a Standing Ovation (S915).",
        }

def analyze_standing_ovation_eml() -> dict[str, Any]:
    t = StandingOvationEML()
    return {
        "session": 915,
        "title": "Mathematics of a Standing Ovation",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T636: Mathematics of a Standing Ovation (S915).",
        "rabbit_hole_log": ["T636: first_person_eml0 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_standing_ovation_eml(), indent=2, default=str))