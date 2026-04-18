"""Session 93 — Fractals Deep: Multifractals, Hausdorff Measure (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.fractals_deep_eml import analyze_fractals_deep_eml
print(json.dumps(analyze_fractals_deep_eml(), indent=2, default=str))
