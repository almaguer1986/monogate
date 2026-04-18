import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.orbs_light_anomalies_eml import analyze_orbs_light_anomalies_eml
result = analyze_orbs_light_anomalies_eml()
print(json.dumps(result, indent=2, default=str))
