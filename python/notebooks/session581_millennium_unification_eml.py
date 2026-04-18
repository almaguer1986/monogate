import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.millennium_unification_eml import analyze_millennium_unification_eml
result = analyze_millennium_unification_eml()
print(json.dumps(result, indent=2, default=str))
