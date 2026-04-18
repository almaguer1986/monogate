"""Session 211 — delta d2 assault eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.delta_d2_assault_eml import analyze_delta_d2_assault_eml
print(json.dumps(analyze_delta_d2_assault_eml(), indent=2, default=str))
