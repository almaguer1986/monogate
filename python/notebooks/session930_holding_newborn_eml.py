import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.holding_newborn_eml import analyze_holding_newborn_eml
result = analyze_holding_newborn_eml()
print(json.dumps(result, indent=2, default=str))