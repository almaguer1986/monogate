import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropical_sat_eml import analyze_tropical_sat_eml
result = analyze_tropical_sat_eml()
print(json.dumps(result, indent=2))
