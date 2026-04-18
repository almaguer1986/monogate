import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_three_constraint_eml import analyze_hodge_three_constraint_eml
result = analyze_hodge_three_constraint_eml()
print(json.dumps(result, indent=2))
