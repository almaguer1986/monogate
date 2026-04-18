import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.discovery_recursive_portrait_eml import analyze_discovery_recursive_portrait_eml
result = analyze_discovery_recursive_portrait_eml()
print(json.dumps(result, indent=2, default=str))
