import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.pvsnp_circuit_complexity_eml import analyze_pvsnp_circuit_complexity_eml
result = analyze_pvsnp_circuit_complexity_eml()
print(json.dumps(result, indent=2, default=str))
