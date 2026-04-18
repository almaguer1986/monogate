import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.lean_formalization_attacks_eml import analyze_lean_formalization_attacks_eml
result = analyze_lean_formalization_attacks_eml()
print(json.dumps(result, indent=2, default=str))
