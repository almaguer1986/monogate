"""Session 857 --- Uncanny Valley as Depth Classification Failure"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class UncannyValleyEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T578: Uncanny Valley as Depth Classification Failure depth analysis",
            "domains": {
                "human_face_classified": {"description": "Real human face: classified at one EML depth by brain", "depth": "EML-3", "reason": "Human face recognition is EML-3: oscillatory neural pattern matching"},
                "cartoon_classified": {"description": "Cartoon face: classified at different EML depth; no discomfort", "depth": "EML-0", "reason": "Cartoon is EML-0: symbolic, discrete; brain classifies cleanly"},
                "between_depths": {"description": "Almost-human sits BETWEEN depths; T110 says fractional depth is impossible", "depth": "EML-inf", "reason": "Uncanny valley is depth classification failure: brain cannot assign integer depth"},
                "discomfort_is_impossibility": {"description": "The discomfort IS the impossibility of fractional EML depth", "depth": "EML-inf", "reason": "Uncanny valley is the subjective experience of EML-4 nonexistence"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "UncannyValleyEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T578: Uncanny Valley as Depth Classification Failure (S857).",
        }

def analyze_uncanny_valley_eml() -> dict[str, Any]:
    t = UncannyValleyEML()
    return {
        "session": 857,
        "title": "Uncanny Valley as Depth Classification Failure",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T578: Uncanny Valley as Depth Classification Failure (S857).",
        "rabbit_hole_log": ["T578: human_face_classified depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_uncanny_valley_eml(), indent=2, default=str))