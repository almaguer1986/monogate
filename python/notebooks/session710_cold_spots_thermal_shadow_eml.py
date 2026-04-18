import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.cold_spots_thermal_shadow_eml import analyze_cold_spots_thermal_shadow_eml
result = analyze_cold_spots_thermal_shadow_eml()
print(json.dumps(result, indent=2, default=str))
