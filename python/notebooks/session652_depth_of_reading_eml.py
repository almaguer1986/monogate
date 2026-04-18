import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.depth_of_reading_eml import analyze_depth_of_reading_eml
result = analyze_depth_of_reading_eml()
print(json.dumps(result, indent=2, default=str))
