import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_conditional_proof_eml import analyze_hodge_conditional_proof_eml
result = analyze_hodge_conditional_proof_eml()
print(json.dumps(result, indent=2, default=str))