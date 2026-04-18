import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.heegner_luc38_eml import analyze_heegner_luc38_eml
result = analyze_heegner_luc38_eml()
print(json.dumps(result, indent=2))
