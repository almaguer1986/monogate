import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_smoke_rings_eml import analyze_ns_smoke_rings_eml
result = analyze_ns_smoke_rings_eml()
print(json.dumps(result, indent=2, default=str))