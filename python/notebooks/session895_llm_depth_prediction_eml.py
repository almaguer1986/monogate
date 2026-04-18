import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.llm_depth_prediction_eml import analyze_llm_depth_prediction_eml
result = analyze_llm_depth_prediction_eml()
print(json.dumps(result, indent=2, default=str))