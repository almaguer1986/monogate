import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.scaling_to_emlinf_eml import analyze_scaling_to_emlinf_eml
result = analyze_scaling_to_emlinf_eml()
print(json.dumps(result, indent=2, default=str))