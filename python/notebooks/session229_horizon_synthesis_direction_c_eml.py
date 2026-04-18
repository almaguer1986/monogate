"""Session 229 — horizon synthesis direction c eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.horizon_synthesis_direction_c_eml import analyze_horizon_synthesis_direction_c_eml
print(json.dumps(analyze_horizon_synthesis_direction_c_eml(), indent=2, default=str))
