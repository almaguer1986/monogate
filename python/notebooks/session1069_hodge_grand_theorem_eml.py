import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_grand_theorem_eml import analyze_hodge_grand_theorem_eml
result = analyze_hodge_grand_theorem_eml()
print(json.dumps(result, indent=2))
