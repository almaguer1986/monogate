import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_breaking_waves_eml import analyze_ns_breaking_waves_eml
result = analyze_ns_breaking_waves_eml()
print(json.dumps(result, indent=2, default=str))