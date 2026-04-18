import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_barriers_depth_eml import analyze_pnp_barriers_depth_eml
result = analyze_pnp_barriers_depth_eml()
print(json.dumps(result, indent=2))
