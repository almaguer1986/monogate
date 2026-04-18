import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_diagonal_argument_eml import analyze_ns_diagonal_argument_eml
result = analyze_ns_diagonal_argument_eml()
print(json.dumps(result, indent=2))
