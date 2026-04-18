import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.ergodic_theory_v2_eml import analyze_ergodic_theory_v2_eml
result = analyze_ergodic_theory_v2_eml()
print(json.dumps(result, indent=2, default=str))
