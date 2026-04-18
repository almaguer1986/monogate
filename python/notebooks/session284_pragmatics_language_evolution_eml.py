import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.pragmatics_language_evolution_eml import analyze_pragmatics_language_evolution_eml
result = analyze_pragmatics_language_evolution_eml()
print(json.dumps(result, indent=2, default=str))
