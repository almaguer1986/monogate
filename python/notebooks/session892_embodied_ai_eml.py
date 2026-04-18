import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.embodied_ai_eml import analyze_embodied_ai_eml
result = analyze_embodied_ai_eml()
print(json.dumps(result, indent=2, default=str))