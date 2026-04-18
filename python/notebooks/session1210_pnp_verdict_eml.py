import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.pnp_verdict_eml import analyze_pnp_verdict_eml
result = analyze_pnp_verdict_eml()
print(json.dumps(result, indent=2))
