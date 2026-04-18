import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ai_consciousness_framework_eml import analyze_ai_consciousness_framework_eml
result = analyze_ai_consciousness_framework_eml()
print(json.dumps(result, indent=2, default=str))