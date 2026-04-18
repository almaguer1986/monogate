import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_boundary_map_eml import analyze_pnp_boundary_map_eml
result = analyze_pnp_boundary_map_eml()
print(json.dumps(result, indent=2))
