import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hardest_curves_eml import analyze_hardest_curves_eml
result = analyze_hardest_curves_eml()
print(json.dumps(result, indent=2))
