import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.coral_reef_ecosystem_eml import analyze_coral_reef_ecosystem_eml
result = analyze_coral_reef_ecosystem_eml()
print(json.dumps(result, indent=2, default=str))
