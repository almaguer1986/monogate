import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_grand_synthesis_eml import analyze_pnp_grand_synthesis_eml
result = analyze_pnp_grand_synthesis_eml()
print(json.dumps(result, indent=2))
