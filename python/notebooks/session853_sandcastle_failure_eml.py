import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.sandcastle_failure_eml import analyze_sandcastle_failure_eml
result = analyze_sandcastle_failure_eml()
print(json.dumps(result, indent=2, default=str))