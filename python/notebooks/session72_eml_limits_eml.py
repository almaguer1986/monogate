"""Session 72 — Limits of EML Approximation (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.eml_limits_eml import analyze_eml_limits

result = analyze_eml_limits()
print(json.dumps(result, indent=2, default=str))
