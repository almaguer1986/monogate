import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_simulation_eml import analyze_quantum_simulation_eml
result = analyze_quantum_simulation_eml()
print(json.dumps(result, indent=2, default=str))