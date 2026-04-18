"""Session 387 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_rh_refinement_eml import analyze_rdl_rh_refinement_eml
result = analyze_rdl_rh_refinement_eml()
print(json.dumps(result, indent=2, default=str))
