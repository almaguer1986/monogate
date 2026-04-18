import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.pvsnp_conditional_proof_eml import analyze_pvsnp_conditional_proof_eml
result = analyze_pvsnp_conditional_proof_eml()
print(json.dumps(result, indent=2, default=str))
