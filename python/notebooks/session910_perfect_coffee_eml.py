import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.perfect_coffee_eml import analyze_perfect_coffee_eml
result = analyze_perfect_coffee_eml()
print(json.dumps(result, indent=2, default=str))