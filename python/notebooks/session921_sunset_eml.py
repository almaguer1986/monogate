import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.sunset_eml import analyze_sunset_eml
result = analyze_sunset_eml()
print(json.dumps(result, indent=2, default=str))