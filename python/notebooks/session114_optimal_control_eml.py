"""Session 114 — Optimal Control & Dynamic Programming (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.optimal_control_eml import analyze_optimal_control_eml
print(json.dumps(analyze_optimal_control_eml(), indent=2, default=str))
