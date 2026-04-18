import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_independence_grand_theorem_eml import analyze_ns_independence_grand_theorem_eml
result = analyze_ns_independence_grand_theorem_eml()
print(json.dumps(result, indent=2))
