import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.meta_atlas_eml import analyze_meta_atlas_eml
result = analyze_meta_atlas_eml()
print(json.dumps(result, indent=2, default=str))
