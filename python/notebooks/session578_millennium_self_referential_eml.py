import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.millennium_self_referential_eml import analyze_millennium_self_referential_eml
result = analyze_millennium_self_referential_eml()
print(json.dumps(result, indent=2, default=str))
