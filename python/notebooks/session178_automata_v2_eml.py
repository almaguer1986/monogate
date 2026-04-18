"""Session 178 — Cellular Automata & Emergent Computation Deep: CA Universality Strata (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.automata_v2_eml import analyze_automata_v2_eml
print(json.dumps(analyze_automata_v2_eml(), indent=2, default=str))
