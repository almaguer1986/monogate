import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.cats_purr_eml import analyze_cats_purr_eml
result = analyze_cats_purr_eml()
print(json.dumps(result, indent=2, default=str))