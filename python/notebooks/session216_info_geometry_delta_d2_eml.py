"""Session 216 — info geometry delta d2 eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.info_geometry_delta_d2_eml import analyze_info_geometry_delta_d2_eml
print(json.dumps(analyze_info_geometry_delta_d2_eml(), indent=2, default=str))
