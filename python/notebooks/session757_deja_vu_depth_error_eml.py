import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.deja_vu_depth_error_eml import analyze_deja_vu_depth_error_eml
result = analyze_deja_vu_depth_error_eml()
print(json.dumps(result, indent=2, default=str))
