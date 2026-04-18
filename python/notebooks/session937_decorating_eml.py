import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.decorating_eml import analyze_decorating_eml
result = analyze_decorating_eml()
print(json.dumps(result, indent=2, default=str))