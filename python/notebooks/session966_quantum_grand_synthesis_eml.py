import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_grand_synthesis_eml import analyze_quantum_grand_synthesis_eml
result = analyze_quantum_grand_synthesis_eml()
print(json.dumps(result, indent=2, default=str))