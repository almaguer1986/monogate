"""Session 164 — notebook script"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.knot_theory_eml import analyze_knot_theory_eml
print(json.dumps(analyze_knot_theory_eml(), indent=2, default=str))
