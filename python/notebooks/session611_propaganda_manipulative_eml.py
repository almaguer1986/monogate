import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.propaganda_manipulative_eml import analyze_propaganda_manipulative_eml
result = analyze_propaganda_manipulative_eml()
print(json.dumps(result, indent=2, default=str))
