import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.observer_effect_consciousness_eml import analyze_observer_effect_consciousness_eml
result = analyze_observer_effect_consciousness_eml()
print(json.dumps(result, indent=2, default=str))
