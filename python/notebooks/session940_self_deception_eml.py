import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.self_deception_eml import analyze_self_deception_eml
result = analyze_self_deception_eml()
print(json.dumps(result, indent=2, default=str))