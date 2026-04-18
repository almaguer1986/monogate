import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.rank2_lean_prep_eml import analyze_rank2_lean_prep_eml
result = analyze_rank2_lean_prep_eml()
print(json.dumps(result, indent=2))
