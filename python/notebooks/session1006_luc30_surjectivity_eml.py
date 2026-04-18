import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.luc30_surjectivity_eml import analyze_luc30_surjectivity_eml
result = analyze_luc30_surjectivity_eml()
print(json.dumps(result, indent=2))
