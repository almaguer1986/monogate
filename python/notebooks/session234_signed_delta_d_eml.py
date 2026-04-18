import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.signed_delta_d_eml import analyze_signed_delta_d_eml
result = analyze_signed_delta_d_eml()
print(json.dumps(result, indent=2, default=str))
