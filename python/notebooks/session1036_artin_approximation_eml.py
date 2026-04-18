import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.artin_approximation_eml import analyze_artin_approximation_eml
result = analyze_artin_approximation_eml()
print(json.dumps(result, indent=2))
