"""Session 482 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.lean_sorry_shadow_depth_theorem_eml import analyze_lean_sorry_shadow_depth_theorem_eml
print(json.dumps(analyze_lean_sorry_shadow_depth_theorem_eml(), indent=2, default=str))
