import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tropical_millennium_barriers_eml import analyze_tropical_millennium_barriers_eml
result = analyze_tropical_millennium_barriers_eml()
print(json.dumps(result, indent=2, default=str))
