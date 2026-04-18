import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tree_phototropism_eml import analyze_tree_phototropism_eml
result = analyze_tree_phototropism_eml()
print(json.dumps(result, indent=2, default=str))