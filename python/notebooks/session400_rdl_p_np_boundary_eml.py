"""Session 400 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_p_np_boundary_eml import analyze_rdl_p_np_boundary_eml
result = analyze_rdl_p_np_boundary_eml()
print(json.dumps(result, indent=2, default=str))
