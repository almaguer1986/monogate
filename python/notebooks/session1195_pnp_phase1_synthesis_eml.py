import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_phase1_synthesis_eml import analyze_pnp_phase1_synthesis_eml
result = analyze_pnp_phase1_synthesis_eml()
print(json.dumps(result, indent=2))
