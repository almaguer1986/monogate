import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.topos_depth_complete_eml import analyze_topos_depth_complete_eml
result = analyze_topos_depth_complete_eml()
print(json.dumps(result, indent=2, default=str))