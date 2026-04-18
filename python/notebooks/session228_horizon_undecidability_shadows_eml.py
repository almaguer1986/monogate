"""Session 228 — horizon undecidability shadows eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.horizon_undecidability_shadows_eml import analyze_horizon_undecidability_shadows_eml
print(json.dumps(analyze_horizon_undecidability_shadows_eml(), indent=2, default=str))
