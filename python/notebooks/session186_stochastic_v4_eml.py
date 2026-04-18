"""Session 186 — Stochastic Processes Deep II: Path-Wise vs Expectation EML Depths (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.stochastic_v4_eml import analyze_stochastic_v4_eml
print(json.dumps(analyze_stochastic_v4_eml(), indent=2, default=str))
