import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.atlas_expansion_13_eml import analyze_atlas_expansion_13_eml
result = analyze_atlas_expansion_13_eml()
print(json.dumps(result, indent=2, default=str))
