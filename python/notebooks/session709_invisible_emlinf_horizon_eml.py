import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.invisible_emlinf_horizon_eml import analyze_invisible_emlinf_horizon_eml
result = analyze_invisible_emlinf_horizon_eml()
print(json.dumps(result, indent=2, default=str))
