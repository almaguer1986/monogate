import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.sha_general_proof_eml import analyze_sha_general_proof_eml
result = analyze_sha_general_proof_eml()
print(json.dumps(result, indent=2))
