import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.fringe_self_referential_eml import analyze_fringe_self_referential_eml
result = analyze_fringe_self_referential_eml()
print(json.dumps(result, indent=2, default=str))
