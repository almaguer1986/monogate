import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_higher_dimensions_eml import analyze_hodge_higher_dimensions_eml
result = analyze_hodge_higher_dimensions_eml()
print(json.dumps(result, indent=2, default=str))