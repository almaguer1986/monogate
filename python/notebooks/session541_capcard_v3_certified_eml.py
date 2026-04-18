import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.capcard_v3_certified_eml import analyze_capcard_v3_certified_eml
result = analyze_capcard_v3_certified_eml()
print(json.dumps(result, indent=2, default=str))
