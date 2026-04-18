import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.shadow_invariant_eml import analyze_shadow_invariant_eml
print(json.dumps(analyze_shadow_invariant_eml(), indent=2, default=str))
