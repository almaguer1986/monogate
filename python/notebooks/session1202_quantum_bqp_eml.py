import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.quantum_bqp_eml import analyze_quantum_bqp_eml
result = analyze_quantum_bqp_eml()
print(json.dumps(result, indent=2))
