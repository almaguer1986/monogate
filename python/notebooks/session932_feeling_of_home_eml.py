import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.feeling_of_home_eml import analyze_feeling_of_home_eml
result = analyze_feeling_of_home_eml()
print(json.dumps(result, indent=2, default=str))