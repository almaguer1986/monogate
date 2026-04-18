import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_adversarial_construction_eml import analyze_hodge_adversarial_construction_eml
result = analyze_hodge_adversarial_construction_eml()
print(json.dumps(result, indent=2))
