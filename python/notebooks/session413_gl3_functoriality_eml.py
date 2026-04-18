import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.gl3_functoriality_eml import analyze_gl3_functoriality_eml
result = analyze_gl3_functoriality_eml()
print(json.dumps(result, indent=2, default=str))
