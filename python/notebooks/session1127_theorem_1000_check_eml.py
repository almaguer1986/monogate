import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.theorem_1000_check_eml import analyze_theorem_1000_check_eml
result = analyze_theorem_1000_check_eml()
print(json.dumps(result, indent=2))
