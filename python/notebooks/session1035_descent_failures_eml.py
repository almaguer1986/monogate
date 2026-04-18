import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.descent_failures_eml import analyze_descent_failures_eml
result = analyze_descent_failures_eml()
print(json.dumps(result, indent=2))
