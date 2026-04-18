import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_partial_regularity_shadow_eml import analyze_ns_partial_regularity_shadow_eml
result = analyze_ns_partial_regularity_shadow_eml()
print(json.dumps(result, indent=2))
