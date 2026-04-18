import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_ym_eml import analyze_pnp_ym_eml
result = analyze_pnp_ym_eml()
print(json.dumps(result, indent=2))
