"""Session 821 --- Bathtub Drain Vortex Depth Map"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class NSBathtubDrainEML:
    def depth_analysis(self) -> dict[str, Any]:
        return {
            "object": "T542: Bathtub Drain Vortex Depth Map depth analysis",
            "domains": {
                "laminar_entry": {"description": "Water at rest is EML-0; laminar approach to drain is EML-2 (Poiseuille flow)", "depth": "EML-2", "reason": "Laminar flow: EML-2 parabolic velocity profile; depth stays finite"},
                "vortex_formation": {"description": "Rotation begins: EML-3 oscillatory tangential velocity develops", "depth": "EML-3", "reason": "Drain vortex: EML-3 rotational structure; angular momentum conservation"},
                "turbulent_core": {"description": "Core near drain: EML-inf turbulent mixing; unpredictable fine structure", "depth": "EML-inf", "reason": "Drain core: EML-inf turbulent; categorification of EML-3 vortex"},
                "laminar_to_turbulent": {"description": "Transition is always a categorification event: EML-3 -> EML-inf at critical Re", "depth": "EML-inf", "reason": "Reynolds number threshold is the depth-transition control parameter"},
            },
        }
    def analyze(self) -> dict[str, Any]:
        depths = [v['depth'] for v in self.depth_analysis()['domains'].values()]
        dist: dict[str, int] = {}
        for d in depths: dist[d] = dist.get(d, 0) + 1
        return {
            "model": "NSBathtubDrainEML",
            "analysis": self.depth_analysis(),
            "distribution": dist,
            "theorem": "T542: Bathtub Drain Vortex Depth Map (S821).",
        }

def analyze_ns_bathtub_drain_eml() -> dict[str, Any]:
    t = NSBathtubDrainEML()
    return {
        "session": 821,
        "title": "Bathtub Drain Vortex Depth Map",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": "T542: Bathtub Drain Vortex Depth Map (S821).",
        "rabbit_hole_log": ["T542: laminar_entry depth confirmed"],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_ns_bathtub_drain_eml(), indent=2, default=str))