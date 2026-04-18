import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ns_universe_signature_eml import analyze_ns_universe_signature_eml
result = analyze_ns_universe_signature_eml()
print(json.dumps(result, indent=2, default=str))