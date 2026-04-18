import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.implications_remaining_eml import analyze_implications_remaining_eml
result = analyze_implications_remaining_eml()
print(json.dumps(result, indent=2, default=str))