"""Session 126 — linguistics deep EML (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.linguistics_deep_eml import analyze_linguistics_deep_eml
print(json.dumps(analyze_linguistics_deep_eml(), indent=2, default=str))
