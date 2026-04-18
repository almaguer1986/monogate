import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.rhythm_meter_oscillation_eml import analyze_rhythm_meter_oscillation_eml
result = analyze_rhythm_meter_oscillation_eml()
print(json.dumps(result, indent=2, default=str))
