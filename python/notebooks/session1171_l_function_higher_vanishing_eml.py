import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.l_function_higher_vanishing_eml import analyze_l_function_higher_vanishing_eml
result = analyze_l_function_higher_vanishing_eml()
print(json.dumps(result, indent=2))
