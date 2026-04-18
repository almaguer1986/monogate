import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.jaffe_witten_axioms_eml import analyze_jaffe_witten_axioms_eml
result = analyze_jaffe_witten_axioms_eml()
print(json.dumps(result, indent=2))
