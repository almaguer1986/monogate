import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.time_dilation_crisis_eml import analyze_time_dilation_crisis_eml
result = analyze_time_dilation_crisis_eml()
print(json.dumps(result, indent=2, default=str))