import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.descent_multiple_cycles_eml import analyze_descent_multiple_cycles_eml
result = analyze_descent_multiple_cycles_eml()
print(json.dumps(result, indent=2))
