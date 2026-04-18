import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.t232_bridge_exact_eml import analyze_t232_bridge_exact_eml
result = analyze_t232_bridge_exact_eml()
print(json.dumps(result, indent=2))
