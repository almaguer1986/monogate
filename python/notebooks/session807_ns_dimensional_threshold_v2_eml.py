import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_dimensional_threshold_v2_eml import analyze_ns_dimensional_threshold_v2_eml
result = analyze_ns_dimensional_threshold_v2_eml()
print(json.dumps(result, indent=2, default=str))