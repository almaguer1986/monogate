import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_blowup_scenarios_eml import analyze_ns_blowup_scenarios_eml
result = analyze_ns_blowup_scenarios_eml()
print(json.dumps(result, indent=2, default=str))
