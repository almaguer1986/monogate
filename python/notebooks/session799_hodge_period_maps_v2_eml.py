import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_period_maps_v2_eml import analyze_hodge_period_maps_v2_eml
result = analyze_hodge_period_maps_v2_eml()
print(json.dumps(result, indent=2, default=str))