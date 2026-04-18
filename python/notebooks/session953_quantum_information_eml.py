import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_information_eml import analyze_quantum_information_eml
result = analyze_quantum_information_eml()
print(json.dumps(result, indent=2, default=str))