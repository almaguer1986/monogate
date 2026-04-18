import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_turing_completeness_proof_eml import analyze_ns_turing_completeness_proof_eml
result = analyze_ns_turing_completeness_proof_eml()
print(json.dumps(result, indent=2))
