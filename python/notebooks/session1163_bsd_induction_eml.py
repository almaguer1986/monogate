import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.bsd_induction_eml import analyze_bsd_induction_eml
result = analyze_bsd_induction_eml()
print(json.dumps(result, indent=2))
