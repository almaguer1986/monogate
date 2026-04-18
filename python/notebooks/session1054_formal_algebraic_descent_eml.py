import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.formal_algebraic_descent_eml import analyze_formal_algebraic_descent_eml
result = analyze_formal_algebraic_descent_eml()
print(json.dumps(result, indent=2))
