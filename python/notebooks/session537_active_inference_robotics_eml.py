import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.active_inference_robotics_eml import analyze_active_inference_robotics_eml
result = analyze_active_inference_robotics_eml()
print(json.dumps(result, indent=2, default=str))
