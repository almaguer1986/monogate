import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_turbulence_cascade_v2_eml import analyze_ns_turbulence_cascade_v2_eml
result = analyze_ns_turbulence_cascade_v2_eml()
print(json.dumps(result, indent=2, default=str))
