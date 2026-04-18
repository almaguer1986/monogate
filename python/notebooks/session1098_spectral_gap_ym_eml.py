import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.spectral_gap_ym_eml import analyze_spectral_gap_ym_eml
result = analyze_spectral_gap_ym_eml()
print(json.dumps(result, indent=2))
