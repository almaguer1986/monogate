"""Session 327 — RH-EML Shadow Refinement"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_shadow_refinement_eml import analyze_rh_eml_shadow_refinement_eml
result = analyze_rh_eml_shadow_refinement_eml()
print(json.dumps(result, indent=2, default=str))
