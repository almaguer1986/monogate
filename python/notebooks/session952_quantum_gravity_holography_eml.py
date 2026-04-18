import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_gravity_holography_eml import analyze_quantum_gravity_holography_eml
result = analyze_quantum_gravity_holography_eml()
print(json.dumps(result, indent=2, default=str))