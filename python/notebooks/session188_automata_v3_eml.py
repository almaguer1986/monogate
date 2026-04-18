"""Session 188 — Cellular Automata Deep II: CA Universality Strata & Emergence Taxonomy (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.automata_v3_eml import analyze_automata_v3_eml
print(json.dumps(analyze_automata_v3_eml(), indent=2, default=str))
