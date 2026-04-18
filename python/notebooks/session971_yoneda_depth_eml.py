import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.yoneda_depth_eml import analyze_yoneda_depth_eml
result = analyze_yoneda_depth_eml()
print(json.dumps(result, indent=2, default=str))