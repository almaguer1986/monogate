"""Session 196 — Δd Charge Angle 5: Knot Theory & Topological Invariants (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.knot_v2_eml import analyze_knot_v2_eml
print(json.dumps(analyze_knot_v2_eml(), indent=2, default=str))
