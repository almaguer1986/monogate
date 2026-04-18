import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_hele_shaw_eml import analyze_ns_hele_shaw_eml
result = analyze_ns_hele_shaw_eml()
print(json.dumps(result, indent=2, default=str))