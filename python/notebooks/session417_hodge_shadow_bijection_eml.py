import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_shadow_bijection_eml import analyze_hodge_shadow_bijection_eml
result = analyze_hodge_shadow_bijection_eml()
print(json.dumps(result, indent=2, default=str))
