import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.therapy_emotional_language_eml import analyze_therapy_emotional_language_eml
result = analyze_therapy_emotional_language_eml()
print(json.dumps(result, indent=2, default=str))
