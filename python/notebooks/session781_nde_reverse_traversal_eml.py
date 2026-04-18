import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.nde_reverse_traversal_eml import analyze_nde_reverse_traversal_eml
result = analyze_nde_reverse_traversal_eml()
print(json.dumps(result, indent=2, default=str))
