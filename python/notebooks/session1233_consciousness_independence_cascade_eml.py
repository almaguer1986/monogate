import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.consciousness_independence_cascade_eml import analyze_consciousness_independence_cascade_eml
result = analyze_consciousness_independence_cascade_eml()
print(json.dumps(result, indent=2))
