import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.crowd_waves_eml import analyze_crowd_waves_eml
result = analyze_crowd_waves_eml()
print(json.dumps(result, indent=2, default=str))