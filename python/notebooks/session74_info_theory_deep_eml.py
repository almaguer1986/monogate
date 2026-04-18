"""Session 74 — Information Theory Deep Dive (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.info_theory_deep_eml import analyze_info_theory_deep_eml

result = analyze_info_theory_deep_eml()
print(json.dumps(result, indent=2, default=str))
