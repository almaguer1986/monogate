import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.cancer_depth_disruption_eml import analyze_cancer_depth_disruption_eml
result = analyze_cancer_depth_disruption_eml()
print(json.dumps(result, indent=2, default=str))
