import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_valid_proof_structure_eml import analyze_pnp_valid_proof_structure_eml
result = analyze_pnp_valid_proof_structure_eml()
print(json.dumps(result, indent=2))
