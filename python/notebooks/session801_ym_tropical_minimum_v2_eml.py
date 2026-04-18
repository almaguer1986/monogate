import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ym_tropical_minimum_v2_eml import analyze_ym_tropical_minimum_v2_eml
result = analyze_ym_tropical_minimum_v2_eml()
print(json.dumps(result, indent=2, default=str))