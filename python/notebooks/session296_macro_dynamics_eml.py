"""Session 296 — Macroeconomic Dynamics"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.macro_dynamics_eml import analyze_macro_dynamics_eml
result = analyze_macro_dynamics_eml()
print(json.dumps(result, indent=2, default=str))
