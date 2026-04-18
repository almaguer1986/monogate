import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.absolute_hodge_classes_eml import analyze_absolute_hodge_classes_eml
result = analyze_absolute_hodge_classes_eml()
print(json.dumps(result, indent=2))
