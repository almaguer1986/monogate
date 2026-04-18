import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.bsd_grand_theorem_eml import analyze_bsd_grand_theorem_eml
result = analyze_bsd_grand_theorem_eml()
print(json.dumps(result, indent=2))
