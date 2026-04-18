import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropical_hodge_groups_attack_eml import analyze_tropical_hodge_groups_attack_eml
result = analyze_tropical_hodge_groups_attack_eml()
print(json.dumps(result, indent=2))
