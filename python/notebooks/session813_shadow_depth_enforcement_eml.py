import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.shadow_depth_enforcement_eml import analyze_shadow_depth_enforcement_eml
result = analyze_shadow_depth_enforcement_eml()
print(json.dumps(result, indent=2, default=str))