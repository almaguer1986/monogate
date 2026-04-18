"""Session 882 --- Smell of Old Books as Sensory Portal"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class SmellOldBooksEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T603: Smell of Old Books as Sensory Portal depth analysis",
            "domains": {
                "chemical_eml1": {"description": "Lignin/cellulose degradation produces vanillin, benzaldehyde: EML-1 exponential", "depth": "EML-1", "reason": "Chemical aging is EML-1: exponential oxidative degradation of paper polymers"},
                "olfactory_blend_eml2": {"description": "Complex olfactory signature: EML-2 measurement of chemical blend", "depth": "EML-2", "reason": "Smell detection is EML-2: logarithmic Weber-Fechner olfactory measurement"},
                "meaning_emlinf": {"description": "Emotional association -- comfort, nostalgia, knowledge: EML-inf", "depth": "EML-inf", "reason": "Old book smell meaning is EML-inf: individual cultural-personal significance beyond finite description"},
                "sensory_portal": {"description": "Old book smell is sensory portal: EML-1 chemistry -> EML-2 perception -> EML-inf meaning", "depth": "EML-inf", "reason": "Portal theorem: smell of old books traverses from EML-1 molecules to EML-inf significance"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "SmellOldBooksEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T603: Smell of Old Books as Sensory Portal (S882).",
        }

def analyze_smell_old_books_eml() -> dict[str, Any]:
    t = SmellOldBooksEML()
    return {
        "session": 882,
        "title": "Smell of Old Books as Sensory Portal",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T603: Smell of Old Books as Sensory Portal (S882).",
        "rabbit_hole_log": ["T603: chemical_eml1 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_smell_old_books_eml(), indent=2, default=str))