import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_combining_routes_eml import analyze_hodge_combining_routes_eml
result = analyze_hodge_combining_routes_eml()
print(json.dumps(result, indent=2))
