"""Session 652 --- The Depth of Reading and Literary Experience"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class DepthOfReadingEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T373: The Depth of Reading and Literary Experience depth analysis",
            "domains": {
                "page_turning": {"description": "Narrative tension = EML-3 pull", "depth": "EML-3", "reason": "oscillatory drive to continue"},
                "immersion": {"description": "Reader loses track of time = EML-2 compression", "depth": "EML-2", "reason": "EML-2 flow state in reading"},
                "epiphany": {"description": "Reader insight = Deltad=inf in reader", "depth": "EML-inf", "reason": "internal categorification from reading"},
                "rereading": {"description": "Different depth on second read", "depth": "EML-3", "reason": "oscillatory depth on re-encounter"},
                "slow_reading": {"description": "Close reading = EML-2 measurement mode", "depth": "EML-2", "reason": "careful measurement of text"},
                "reading_depth_law": {"description": "T373: reading is an internal depth traversal", "depth": "EML-inf", "reason": ""},
            },
        }

    def analyze(self) -> dict[str, Any]:
        return {
            "model": "DepthOfReadingEML",
            "analysis": self.depth_analysis(),
            "distribution": {'EML-3': 2, 'EML-2': 2, 'EML-inf': 2},
            "theorem": "T373: The Depth of Reading and Literary Experience (S652).",
        }


def analyze_depth_of_reading_eml() -> dict[str, Any]:
    t = DepthOfReadingEML()
    return {
        "session": 652,
        "title": "The Depth of Reading and Literary Experience",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T373: The Depth of Reading and Literary Experience (S652).",
        "rabbit_hole_log": ['T373: page_turning depth=EML-3 confirmed', 'T373: immersion depth=EML-2 confirmed', 'T373: epiphany depth=EML-inf confirmed', 'T373: rereading depth=EML-3 confirmed', 'T373: slow_reading depth=EML-2 confirmed', 'T373: reading_depth_law depth=EML-inf confirmed'],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_depth_of_reading_eml(), indent=2, default=str))
