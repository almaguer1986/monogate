import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.umami_taste_eml import analyze_umami_taste_eml
result = analyze_umami_taste_eml()
print(json.dumps(result, indent=2, default=str))