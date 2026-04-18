"""Session 170 — notebook script"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.grand_synthesis_10_eml import analyze_grand_synthesis_10_eml
print(json.dumps(analyze_grand_synthesis_10_eml(), indent=2, default=str))
