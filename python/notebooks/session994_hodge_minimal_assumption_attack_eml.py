import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_minimal_assumption_attack_eml import analyze_hodge_minimal_assumption_attack_eml
result = analyze_hodge_minimal_assumption_attack_eml()
print(json.dumps(result, indent=2, default=str))