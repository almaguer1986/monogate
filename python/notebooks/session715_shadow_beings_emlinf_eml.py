import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.shadow_beings_emlinf_eml import analyze_shadow_beings_emlinf_eml
result = analyze_shadow_beings_emlinf_eml()
print(json.dumps(result, indent=2, default=str))
