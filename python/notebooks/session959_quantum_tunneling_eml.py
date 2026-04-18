import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_tunneling_eml import analyze_quantum_tunneling_eml
result = analyze_quantum_tunneling_eml()
print(json.dumps(result, indent=2, default=str))