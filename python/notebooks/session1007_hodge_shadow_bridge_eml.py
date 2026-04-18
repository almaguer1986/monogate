import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_shadow_bridge_eml import analyze_hodge_shadow_bridge_eml
result = analyze_hodge_shadow_bridge_eml()
print(json.dumps(result, indent=2))
