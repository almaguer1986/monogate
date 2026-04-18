import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_spectral_unitarity_eml import analyze_hodge_spectral_unitarity_eml
result = analyze_hodge_spectral_unitarity_eml()
print(json.dumps(result, indent=2))
