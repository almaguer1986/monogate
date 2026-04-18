import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.lattice_continuum_descent_eml import analyze_lattice_continuum_descent_eml
result = analyze_lattice_continuum_descent_eml()
print(json.dumps(result, indent=2))
