import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_phase2_synthesis_eml import analyze_ns_phase2_synthesis_eml
result = analyze_ns_phase2_synthesis_eml()
print(json.dumps(result, indent=2))
