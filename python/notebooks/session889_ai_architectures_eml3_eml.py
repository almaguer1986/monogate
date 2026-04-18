import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ai_architectures_eml3_eml import analyze_ai_architectures_eml3_eml
result = analyze_ai_architectures_eml3_eml()
print(json.dumps(result, indent=2, default=str))