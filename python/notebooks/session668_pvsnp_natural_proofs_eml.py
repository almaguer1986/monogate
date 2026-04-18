import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.pvsnp_natural_proofs_eml import analyze_pvsnp_natural_proofs_eml
result = analyze_pvsnp_natural_proofs_eml()
print(json.dumps(result, indent=2, default=str))
