import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ns_ym_comparison_eml import analyze_ns_ym_comparison_eml
result = analyze_ns_ym_comparison_eml()
print(json.dumps(result, indent=2))
