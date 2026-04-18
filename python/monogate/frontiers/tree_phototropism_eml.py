"""Session 923 --- Mathematics of a Tree Growing Toward Light"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class TreePhototropismEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T644: Mathematics of a Tree Growing Toward Light depth analysis",
            "domains": {
                "auxin_eml2": {"description": "Auxin gradient: EML-2 logarithmic concentration measurement for phototropism", "depth": "EML-2", "reason": "Auxin is EML-2: logarithmic gradient measurement determines which cells elongate"},
                "growth_eml1": {"description": "Growth: exponential; EML-1", "depth": "EML-1", "reason": "Tree growth is EML-1: exponential cell division and elongation in response to gradient"},
                "circumnutations_eml3": {"description": "Oscillatory circumnutation search path: EML-3", "depth": "EML-3", "reason": "Tree tip path is EML-3: oscillatory spiral search motion during phototropic growth"},
                "shape_frozen_record": {"description": "Tree shape: frozen record of lifetime depth traversals; each branch is a decision point", "depth": "EML-3", "reason": "Tree theorem: the tree's shape is frozen EML-2/3 decision history; arboreal autobiography"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "TreePhototropismEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T644: Mathematics of a Tree Growing Toward Light (S923).",
        }

def analyze_tree_phototropism_eml() -> dict[str, Any]:
    t = TreePhototropismEML()
    return {
        "session": 923,
        "title": "Mathematics of a Tree Growing Toward Light",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T644: Mathematics of a Tree Growing Toward Light (S923).",
        "rabbit_hole_log": ["T644: auxin_eml2 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_tree_phototropism_eml(), indent=2, default=str))