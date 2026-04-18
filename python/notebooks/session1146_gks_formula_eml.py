import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.gks_formula_eml import analyze_gks_formula_eml
result = analyze_gks_formula_eml()
print(json.dumps(result, indent=2))
