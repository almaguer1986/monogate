import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ym_asymptotic_freedom_eml import analyze_ym_asymptotic_freedom_eml
result = analyze_ym_asymptotic_freedom_eml()
print(json.dumps(result, indent=2, default=str))
