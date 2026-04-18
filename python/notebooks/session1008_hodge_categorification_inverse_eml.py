import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_categorification_inverse_eml import analyze_hodge_categorification_inverse_eml
result = analyze_hodge_categorification_inverse_eml()
print(json.dumps(result, indent=2))
