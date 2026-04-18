import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.adjunction_depth_eml import analyze_adjunction_depth_eml
result = analyze_adjunction_depth_eml()
print(json.dumps(result, indent=2, default=str))