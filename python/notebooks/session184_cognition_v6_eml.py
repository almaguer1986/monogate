"""Session 184 — Consciousness & Cognition Deep III: Qualia, Binding & The Hard Problem (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.cognition_v6_eml import analyze_cognition_v6_eml
print(json.dumps(analyze_cognition_v6_eml(), indent=2, default=str))
