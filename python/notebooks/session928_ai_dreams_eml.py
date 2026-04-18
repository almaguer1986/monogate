import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ai_dreams_eml import analyze_ai_dreams_eml
result = analyze_ai_dreams_eml()
print(json.dumps(result, indent=2, default=str))