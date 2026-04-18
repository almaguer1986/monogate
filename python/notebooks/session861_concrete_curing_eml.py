import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.concrete_curing_eml import analyze_concrete_curing_eml
result = analyze_concrete_curing_eml()
print(json.dumps(result, indent=2, default=str))