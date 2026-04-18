import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.mass_gap_moduli_geometry_eml import analyze_mass_gap_moduli_geometry_eml
result = analyze_mass_gap_moduli_geometry_eml()
print(json.dumps(result, indent=2))
