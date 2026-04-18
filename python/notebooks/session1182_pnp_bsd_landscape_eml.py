import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_bsd_landscape_eml import analyze_pnp_bsd_landscape_eml
result = analyze_pnp_bsd_landscape_eml()
print(json.dumps(result, indent=2))
