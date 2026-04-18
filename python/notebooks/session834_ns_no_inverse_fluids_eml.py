import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_no_inverse_fluids_eml import analyze_ns_no_inverse_fluids_eml
result = analyze_ns_no_inverse_fluids_eml()
print(json.dumps(result, indent=2, default=str))