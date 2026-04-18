import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.yangmills_tropical_gauge_eml import analyze_yangmills_tropical_gauge_eml
result = analyze_yangmills_tropical_gauge_eml()
print(json.dumps(result, indent=2, default=str))
