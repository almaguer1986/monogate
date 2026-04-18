import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_euler_vs_ns_eml import analyze_ns_euler_vs_ns_eml
result = analyze_ns_euler_vs_ns_eml()
print(json.dumps(result, indent=2, default=str))