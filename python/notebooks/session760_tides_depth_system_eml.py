import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tides_depth_system_eml import analyze_tides_depth_system_eml
result = analyze_tides_depth_system_eml()
print(json.dumps(result, indent=2, default=str))
