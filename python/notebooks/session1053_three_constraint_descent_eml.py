import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.three_constraint_descent_eml import analyze_three_constraint_descent_eml
result = analyze_three_constraint_descent_eml()
print(json.dumps(result, indent=2))
