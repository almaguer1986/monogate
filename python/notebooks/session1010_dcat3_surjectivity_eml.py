import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.dcat3_surjectivity_eml import analyze_dcat3_surjectivity_eml
result = analyze_dcat3_surjectivity_eml()
print(json.dumps(result, indent=2))
