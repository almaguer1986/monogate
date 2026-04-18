import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_formalization_eml import analyze_pnp_formalization_eml
result = analyze_pnp_formalization_eml()
print(json.dumps(result, indent=2))
