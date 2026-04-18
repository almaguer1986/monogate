import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.gl3_grh_cascade_eml import analyze_gl3_grh_cascade_eml
result = analyze_gl3_grh_cascade_eml()
print(json.dumps(result, indent=2, default=str))
