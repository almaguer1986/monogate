import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.motivic_bridge_bsd_eml import analyze_motivic_bridge_bsd_eml
result = analyze_motivic_bridge_bsd_eml()
print(json.dumps(result, indent=2))
