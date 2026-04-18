import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_viscosity_escape_eml import analyze_ns_viscosity_escape_eml
result = analyze_ns_viscosity_escape_eml()
print(json.dumps(result, indent=2))
