import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.eml_minimality_2_eml import analyze_eml_minimality_2_eml
result = analyze_eml_minimality_2_eml()
print(json.dumps(result, indent=2, default=str))
