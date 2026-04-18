import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.yangmills_mass_gap_type2_eml import analyze_yangmills_mass_gap_type2_eml
result = analyze_yangmills_mass_gap_type2_eml()
print(json.dumps(result, indent=2, default=str))
