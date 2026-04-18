import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.permanent_determinant_eml import analyze_permanent_determinant_eml
result = analyze_permanent_determinant_eml()
print(json.dumps(result, indent=2))
