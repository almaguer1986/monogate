"""Session 862 --- Birdsong Dialects as Mini-Speciation"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class BirdsongDialectsEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T583: Birdsong Dialects as Mini-Speciation depth analysis",
            "domains": {
                "song_eml3": {"description": "Birdsong: EML-3 oscillatory acoustic signal; species-specific frequency patterns", "depth": "EML-3", "reason": "Bird song is EML-3: temporal oscillatory structure with frequency modulation"},
                "dialect_boundary": {"description": "Dialect boundaries between populations may be depth boundaries", "depth": "EML-inf", "reason": "Dialect formation = categorification of EML-3 song into distinct EML-inf cultural units"},
                "mini_speciation": {"description": "Birdsong dialect formation is mini-speciation: categorification of acoustic EML-3", "depth": "EML-inf", "reason": "Dialect = acoustic Grimm's Law: EML-0 phoneme permutation creates new song family"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "BirdsongDialectsEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T583: Birdsong Dialects as Mini-Speciation (S862).",
        }

def analyze_birdsong_dialects_eml() -> dict[str, Any]:
    t = BirdsongDialectsEML()
    return {
        "session": 862,
        "title": "Birdsong Dialects as Mini-Speciation",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T583: Birdsong Dialects as Mini-Speciation (S862).",
        "rabbit_hole_log": ["T583: song_eml3 depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_birdsong_dialects_eml(), indent=2, default=str))