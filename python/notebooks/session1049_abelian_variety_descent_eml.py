import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.abelian_variety_descent_eml import analyze_abelian_variety_descent_eml
result = analyze_abelian_variety_descent_eml()
print(json.dumps(result, indent=2))
