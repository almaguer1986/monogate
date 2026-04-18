import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.neural_scaling_shadow_eml import analyze_neural_scaling_shadow_eml
print(json.dumps(analyze_neural_scaling_shadow_eml(), indent=2, default=str))
