import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.soil_ecosystem_depth_eml import analyze_soil_ecosystem_depth_eml
result = analyze_soil_ecosystem_depth_eml()
print(json.dumps(result, indent=2, default=str))
