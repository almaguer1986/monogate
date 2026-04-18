import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.fringe_predictive_model_eml import analyze_fringe_predictive_model_eml
result = analyze_fringe_predictive_model_eml()
print(json.dumps(result, indent=2, default=str))
