import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.uncanny_valley_eml import analyze_uncanny_valley_eml
result = analyze_uncanny_valley_eml()
print(json.dumps(result, indent=2, default=str))