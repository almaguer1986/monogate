import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ai_observer_effect_eml import analyze_ai_observer_effect_eml
result = analyze_ai_observer_effect_eml()
print(json.dumps(result, indent=2, default=str))