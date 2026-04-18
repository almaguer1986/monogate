"""Session 79 — Differential Galois: Nonlinear ODEs & Painlevé (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.nonlinear_galois_eml import analyze_nonlinear_galois_eml
print(json.dumps(analyze_nonlinear_galois_eml(), indent=2, default=str))
