"""Session 83 — Limits of Approximation Deep (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.approx_limits_deep_eml import analyze_approx_limits_deep_eml
print(json.dumps(analyze_approx_limits_deep_eml(), indent=2, default=str))
