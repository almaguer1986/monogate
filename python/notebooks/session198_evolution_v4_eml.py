"""Session 198 — Δd Charge Angle 7: Evolutionary & Biological Phase Transitions (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.evolution_v4_eml import analyze_evolution_v4_eml
print(json.dumps(analyze_evolution_v4_eml(), indent=2, default=str))
