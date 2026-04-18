import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tropical_hodge_eml import analyze_tropical_hodge_eml
result = analyze_tropical_hodge_eml()
print(json.dumps(result, indent=2, default=str))