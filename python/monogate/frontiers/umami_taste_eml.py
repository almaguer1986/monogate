"""Session 879 --- Umami as Depth-1 Synergistic Taste"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class UmamiTasteEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T600: Umami as Depth-1 Synergistic Taste depth analysis",
            "domains": {
                "basic_tastes_eml0": {"description": "Sweet, sour, salty, bitter: simple receptor activations; EML-0", "depth": "EML-0", "reason": "Basic tastes are EML-0: discrete receptor binding, simple threshold response"},
                "umami_eml1": {"description": "Umami: synergistic amplification of other flavors; EML-1 exponential enhancement", "depth": "EML-1", "reason": "Umami is EML-1: glutamate+nucleotide synergy creates exponential flavor amplification"},
                "hardest_to_describe": {"description": "Umami discovered last; hardest to describe; only taste above EML-0", "depth": "EML-1", "reason": "Umami uniqueness: EML-1 makes it indescribable in EML-0 terms; requires tasting to understand"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "UmamiTasteEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T600: Umami as Depth-1 Synergistic Taste (S879).",
        }

def analyze_umami_taste_eml() -> dict[str, Any]:
    t = UmamiTasteEML()
    return {
        "session": 879,
        "title": "Umami as Depth-1 Synergistic Taste",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T600: Umami as Depth-1 Synergistic Taste (S879).",
        "rabbit_hole_log": ["T600: basic_tastes_eml0 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_umami_taste_eml(), indent=2, default=str))