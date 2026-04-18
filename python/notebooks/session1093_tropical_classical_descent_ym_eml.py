import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropical_classical_descent_ym_eml import analyze_tropical_classical_descent_ym_eml
result = analyze_tropical_classical_descent_ym_eml()
print(json.dumps(result, indent=2))
