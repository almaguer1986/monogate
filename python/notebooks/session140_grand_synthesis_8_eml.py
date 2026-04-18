"""Session 140 — Grand Synthesis VIII: Limits, Boundaries & The Horizon (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.grand_synthesis_8_eml import analyze_grand_synthesis_8_eml
print(json.dumps(analyze_grand_synthesis_8_eml(), indent=2, default=str))
