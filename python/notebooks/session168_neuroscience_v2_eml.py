"""Session 168 — notebook script"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.neuroscience_v2_eml import analyze_neuroscience_v2_eml
print(json.dumps(analyze_neuroscience_v2_eml(), indent=2, default=str))
