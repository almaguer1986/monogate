import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ym_counterexample_eml import analyze_ym_counterexample_eml
result = analyze_ym_counterexample_eml()
print(json.dumps(result, indent=2))
