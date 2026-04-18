import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ym_mass_gap_tropical_eml import analyze_ym_mass_gap_tropical_eml
result = analyze_ym_mass_gap_tropical_eml()
print(json.dumps(result, indent=2, default=str))
