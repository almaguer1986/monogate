import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.lean_ecl_proof_eml import analyze_lean_ecl_proof_eml
result = analyze_lean_ecl_proof_eml()
print(json.dumps(result, indent=2, default=str))
