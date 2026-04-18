import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.self_referential_assault_v2_eml import analyze_self_referential_assault_v2_eml
result = analyze_self_referential_assault_v2_eml()
print(json.dumps(result, indent=2, default=str))