"""Session 137 — Climate Deep II: Feedback, Tipping Points & Paleoclimate (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.climate_v2_eml import analyze_climate_v2_eml
print(json.dumps(analyze_climate_v2_eml(), indent=2, default=str))
