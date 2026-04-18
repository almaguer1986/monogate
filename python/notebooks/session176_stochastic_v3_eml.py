"""Session 176 — Stochastic Processes & Path Integrals Deep: Itô vs Stratonovich (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.stochastic_v3_eml import analyze_stochastic_v3_eml
print(json.dumps(analyze_stochastic_v3_eml(), indent=2, default=str))
