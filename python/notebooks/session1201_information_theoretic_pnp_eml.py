import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.information_theoretic_pnp_eml import analyze_information_theoretic_pnp_eml
result = analyze_information_theoretic_pnp_eml()
print(json.dumps(result, indent=2))
