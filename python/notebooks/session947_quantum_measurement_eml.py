import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_measurement_eml import analyze_quantum_measurement_eml
result = analyze_quantum_measurement_eml()
print(json.dumps(result, indent=2, default=str))