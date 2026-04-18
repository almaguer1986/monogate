import json, sys
sys.path.insert(0, 'python')
from monogate.frontiers.gl3_synthesis_eml import analyze_gl3_synthesis_eml
result = analyze_gl3_synthesis_eml()
print(json.dumps(result, indent=2, default=str))
