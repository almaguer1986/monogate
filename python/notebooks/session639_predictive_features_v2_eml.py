import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.predictive_features_v2_eml import analyze_predictive_features_v2_eml
result = analyze_predictive_features_v2_eml()
print(json.dumps(result, indent=2, default=str))
