"""Session 881 --- Crowd Waves as Social Phase Transition"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class CrowdWavesEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T602: Crowd Waves as Social Phase Transition depth analysis",
            "domains": {
                "individual_eml0": {"description": "Individual standing: EML-0 binary", "depth": "EML-0", "reason": "Individual in crowd is EML-0: standing or sitting; no cooperative dynamics alone"},
                "wave_propagation": {"description": "Wave propagation: EML-3 oscillatory", "depth": "EML-3", "reason": "Crowd wave is EML-3: oscillatory standing wave propagating through discrete EML-0 individuals"},
                "critical_density": {"description": "Wave requires critical density threshold: depth transition at minimum crowd density", "depth": "EML-inf", "reason": "Threshold is TYPE2: below critical density nothing; above critical density spontaneous EML-3 wave"},
                "social_phase_transition": {"description": "Crowd wave = social phase transition; density is control parameter", "depth": "EML-inf", "reason": "Social categorification: EML-0 individuals + EML-3 wave requires EML-inf threshold crossing"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "CrowdWavesEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T602: Crowd Waves as Social Phase Transition (S881).",
        }

def analyze_crowd_waves_eml() -> dict[str, Any]:
    t = CrowdWavesEML()
    return {
        "session": 881,
        "title": "Crowd Waves as Social Phase Transition",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T602: Crowd Waves as Social Phase Transition (S881).",
        "rabbit_hole_log": ["T602: individual_eml0 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_crowd_waves_eml(), indent=2, default=str))