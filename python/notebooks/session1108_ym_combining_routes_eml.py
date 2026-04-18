import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ym_combining_routes_eml import analyze_ym_combining_routes_eml
result = analyze_ym_combining_routes_eml()
print(json.dumps(result, indent=2))
