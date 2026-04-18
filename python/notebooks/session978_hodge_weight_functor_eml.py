import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_weight_functor_eml import analyze_hodge_weight_functor_eml
result = analyze_hodge_weight_functor_eml()
print(json.dumps(result, indent=2, default=str))