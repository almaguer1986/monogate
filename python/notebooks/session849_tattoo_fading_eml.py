import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tattoo_fading_eml import analyze_tattoo_fading_eml
result = analyze_tattoo_fading_eml()
print(json.dumps(result, indent=2, default=str))