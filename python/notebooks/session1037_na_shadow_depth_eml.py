import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.na_shadow_depth_eml import analyze_na_shadow_depth_eml
result = analyze_na_shadow_depth_eml()
print(json.dumps(result, indent=2))
