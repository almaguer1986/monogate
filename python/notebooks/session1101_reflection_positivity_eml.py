import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.reflection_positivity_eml import analyze_reflection_positivity_eml
result = analyze_reflection_positivity_eml()
print(json.dumps(result, indent=2))
