import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.higher_category_theory_eml import analyze_higher_category_theory_eml
result = analyze_higher_category_theory_eml()
print(json.dumps(result, indent=2, default=str))
