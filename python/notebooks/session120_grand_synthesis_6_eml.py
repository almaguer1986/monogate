"""Session 120 — Grand Synthesis VI: The EML Meta-Architecture (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.grand_synthesis_6_eml import analyze_grand_synthesis_6_eml
print(json.dumps(analyze_grand_synthesis_6_eml(), indent=2, default=str))
