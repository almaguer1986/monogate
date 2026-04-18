import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_turing_complete_eml import analyze_ns_turing_complete_eml
result = analyze_ns_turing_complete_eml()
print(json.dumps(result, indent=2))
