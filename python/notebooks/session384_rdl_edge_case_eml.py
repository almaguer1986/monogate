"""Session 384 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_edge_case_eml import analyze_rdl_edge_case_eml
result = analyze_rdl_edge_case_eml()
print(json.dumps(result, indent=2, default=str))
