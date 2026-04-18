import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_computational_eml import analyze_hodge_computational_eml
result = analyze_hodge_computational_eml()
print(json.dumps(result, indent=2))
