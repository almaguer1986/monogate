import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.eml3_time_oscillatory_rhythm_eml import analyze_eml3_time_oscillatory_rhythm_eml
result = analyze_eml3_time_oscillatory_rhythm_eml()
print(json.dumps(result, indent=2, default=str))
