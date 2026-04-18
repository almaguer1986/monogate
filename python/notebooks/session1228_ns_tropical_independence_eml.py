import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_tropical_independence_eml import analyze_ns_tropical_independence_eml
result = analyze_ns_tropical_independence_eml()
print(json.dumps(result, indent=2))
