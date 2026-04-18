import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_river_heraclitus_eml import analyze_ns_river_heraclitus_eml
result = analyze_ns_river_heraclitus_eml()
print(json.dumps(result, indent=2, default=str))