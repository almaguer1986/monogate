import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.bsd_ym_eml import analyze_bsd_ym_eml
result = analyze_bsd_ym_eml()
print(json.dumps(result, indent=2))
