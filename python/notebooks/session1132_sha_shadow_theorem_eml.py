import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.sha_shadow_theorem_eml import analyze_sha_shadow_theorem_eml
result = analyze_sha_shadow_theorem_eml()
print(json.dumps(result, indent=2))
