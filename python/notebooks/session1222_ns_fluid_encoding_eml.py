import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_fluid_encoding_eml import analyze_ns_fluid_encoding_eml
result = analyze_ns_fluid_encoding_eml()
print(json.dumps(result, indent=2))
