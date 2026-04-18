import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropical_bsd_rank2_eml import analyze_tropical_bsd_rank2_eml
result = analyze_tropical_bsd_rank2_eml()
print(json.dumps(result, indent=2))
