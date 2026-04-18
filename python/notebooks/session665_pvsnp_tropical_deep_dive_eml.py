import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.pvsnp_tropical_deep_dive_eml import analyze_pvsnp_tropical_deep_dive_eml
result = analyze_pvsnp_tropical_deep_dive_eml()
print(json.dumps(result, indent=2, default=str))
