"""Session 121 — consciousness deep EML (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.consciousness_deep_eml import analyze_consciousness_deep_eml
print(json.dumps(analyze_consciousness_deep_eml(), indent=2, default=str))
