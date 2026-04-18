import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.dna_depth_traversal_eml import analyze_dna_depth_traversal_eml
result = analyze_dna_depth_traversal_eml()
print(json.dumps(result, indent=2, default=str))
