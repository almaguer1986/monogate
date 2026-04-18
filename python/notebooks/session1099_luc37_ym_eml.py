import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.luc37_ym_eml import analyze_luc37_ym_eml
result = analyze_luc37_ym_eml()
print(json.dumps(result, indent=2))
