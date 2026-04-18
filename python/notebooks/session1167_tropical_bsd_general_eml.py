import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropical_bsd_general_eml import analyze_tropical_bsd_general_eml
result = analyze_tropical_bsd_general_eml()
print(json.dumps(result, indent=2))
