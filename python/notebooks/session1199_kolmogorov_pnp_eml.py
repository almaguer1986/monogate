import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.kolmogorov_pnp_eml import analyze_kolmogorov_pnp_eml
result = analyze_kolmogorov_pnp_eml()
print(json.dumps(result, indent=2))
