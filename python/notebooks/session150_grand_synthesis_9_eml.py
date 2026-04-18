"""Session 150 — Grand Synthesis IX: Testing the Horizon Theorem & What Lies Beyond (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.grand_synthesis_9_eml import analyze_grand_synthesis_9_eml
print(json.dumps(analyze_grand_synthesis_9_eml(), indent=2, default=str))
