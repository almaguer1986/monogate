"""Session 194 — Δd Charge Angle 3: Stochastic & Path Integral Asymmetry (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.stochastic_v5_eml import analyze_stochastic_v5_eml
print(json.dumps(analyze_stochastic_v5_eml(), indent=2, default=str))
