import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_ym_functorial_eml import analyze_hodge_ym_functorial_eml
result = analyze_hodge_ym_functorial_eml()
print(json.dumps(result, indent=2))
