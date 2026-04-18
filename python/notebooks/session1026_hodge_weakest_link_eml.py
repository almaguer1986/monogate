import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_weakest_link_eml import analyze_hodge_weakest_link_eml
result = analyze_hodge_weakest_link_eml()
print(json.dumps(result, indent=2))
