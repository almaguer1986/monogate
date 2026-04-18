import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.neural_scaling_v2_eml import analyze_neural_scaling_v2_eml
result = analyze_neural_scaling_v2_eml()
print(json.dumps(result, indent=2, default=str))
