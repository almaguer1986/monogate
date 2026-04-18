import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.mechanism_design_eml import analyze_mechanism_design_eml
result = analyze_mechanism_design_eml()
print(json.dumps(result, indent=2, default=str))
