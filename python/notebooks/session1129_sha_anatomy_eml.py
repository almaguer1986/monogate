import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.sha_anatomy_eml import analyze_sha_anatomy_eml
result = analyze_sha_anatomy_eml()
print(json.dumps(result, indent=2))
