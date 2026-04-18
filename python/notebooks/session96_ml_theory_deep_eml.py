"""Session 96 — ML Theory Deep: Grokking, Emergence & Scaling Laws (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.ml_theory_deep_eml import analyze_ml_theory_deep_eml
print(json.dumps(analyze_ml_theory_deep_eml(), indent=2, default=str))
