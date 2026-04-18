import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_surjectivity_anatomy_eml import analyze_hodge_surjectivity_anatomy_eml
result = analyze_hodge_surjectivity_anatomy_eml()
print(json.dumps(result, indent=2))
