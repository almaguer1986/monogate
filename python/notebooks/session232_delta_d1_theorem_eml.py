import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.delta_d1_theorem_eml import analyze_delta_d1_theorem_eml
result = analyze_delta_d1_theorem_eml()
print(json.dumps(result, indent=2, default=str))
