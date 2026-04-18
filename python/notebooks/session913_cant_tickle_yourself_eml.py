import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.cant_tickle_yourself_eml import analyze_cant_tickle_yourself_eml
result = analyze_cant_tickle_yourself_eml()
print(json.dumps(result, indent=2, default=str))