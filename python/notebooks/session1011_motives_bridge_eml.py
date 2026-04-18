import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.motives_bridge_eml import analyze_motives_bridge_eml
result = analyze_motives_bridge_eml()
print(json.dumps(result, indent=2))
