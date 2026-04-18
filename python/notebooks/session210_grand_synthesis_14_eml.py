"""Session 210 — grand synthesis 14 eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.grand_synthesis_14_eml import analyze_grand_synthesis_14_eml
print(json.dumps(analyze_grand_synthesis_14_eml(), indent=2, default=str))
