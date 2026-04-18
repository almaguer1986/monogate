import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_bathtub_drain_eml import analyze_ns_bathtub_drain_eml
result = analyze_ns_bathtub_drain_eml()
print(json.dumps(result, indent=2, default=str))