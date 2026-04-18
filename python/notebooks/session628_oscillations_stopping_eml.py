import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.oscillations_stopping_eml import analyze_oscillations_stopping_eml
result = analyze_oscillations_stopping_eml()
print(json.dumps(result, indent=2, default=str))
