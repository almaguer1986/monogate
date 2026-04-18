import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.proof_theory_ordinal_eml import analyze_proof_theory_ordinal_eml
result = analyze_proof_theory_ordinal_eml()
print(json.dumps(result, indent=2, default=str))
