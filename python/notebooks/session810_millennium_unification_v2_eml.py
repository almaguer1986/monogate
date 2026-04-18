import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.millennium_unification_v2_eml import analyze_millennium_unification_v2_eml
result = analyze_millennium_unification_v2_eml()
print(json.dumps(result, indent=2, default=str))