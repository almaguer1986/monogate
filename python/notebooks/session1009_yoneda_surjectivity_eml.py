import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.yoneda_surjectivity_eml import analyze_yoneda_surjectivity_eml
result = analyze_yoneda_surjectivity_eml()
print(json.dumps(result, indent=2))
