import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.info_geometry_self_ref_eml import analyze_info_geometry_self_ref_eml
result = analyze_info_geometry_self_ref_eml()
print(json.dumps(result, indent=2, default=str))
