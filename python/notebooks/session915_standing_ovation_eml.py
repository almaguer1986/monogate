import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.standing_ovation_eml import analyze_standing_ovation_eml
result = analyze_standing_ovation_eml()
print(json.dumps(result, indent=2, default=str))