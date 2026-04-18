import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_weather_prediction_shadow_eml import analyze_ns_weather_prediction_shadow_eml
result = analyze_ns_weather_prediction_shadow_eml()
print(json.dumps(result, indent=2, default=str))