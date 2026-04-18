import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.quantum_invisible_collapse_eml import analyze_quantum_invisible_collapse_eml
result = analyze_quantum_invisible_collapse_eml()
print(json.dumps(result, indent=2, default=str))
