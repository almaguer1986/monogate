import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.grand_synthesis_predictive_final_eml import analyze_grand_synthesis_predictive_final_eml
result = analyze_grand_synthesis_predictive_final_eml()
print(json.dumps(result, indent=2, default=str))
