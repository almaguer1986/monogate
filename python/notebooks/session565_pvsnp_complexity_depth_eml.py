import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pvsnp_complexity_depth_eml import analyze_pvsnp_complexity_depth_eml
result = analyze_pvsnp_complexity_depth_eml()
print(json.dumps(result, indent=2, default=str))
