"""Session 458 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.shadow_depth_derived_eml import analyze_shadow_depth_derived_eml
print(json.dumps(analyze_shadow_depth_derived_eml(), indent=2, default=str))
