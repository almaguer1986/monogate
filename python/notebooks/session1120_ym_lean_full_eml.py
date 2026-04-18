import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ym_lean_full_eml import analyze_ym_lean_full_eml
result = analyze_ym_lean_full_eml()
print(json.dumps(result, indent=2))
