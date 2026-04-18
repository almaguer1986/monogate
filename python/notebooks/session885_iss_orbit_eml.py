import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.iss_orbit_eml import analyze_iss_orbit_eml
result = analyze_iss_orbit_eml()
print(json.dumps(result, indent=2, default=str))