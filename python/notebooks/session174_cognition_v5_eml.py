"""Session 174 — Consciousness & Cognition Deep: IIT, Hard Problem & Qualia Strata (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.cognition_v5_eml import analyze_cognition_v5_eml
print(json.dumps(analyze_cognition_v5_eml(), indent=2, default=str))
