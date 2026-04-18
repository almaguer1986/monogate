import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_tropical_vorticity_eml import analyze_ns_tropical_vorticity_eml
result = analyze_ns_tropical_vorticity_eml()
print(json.dumps(result, indent=2, default=str))