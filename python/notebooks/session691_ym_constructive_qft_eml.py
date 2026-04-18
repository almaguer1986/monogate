import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ym_constructive_qft_eml import analyze_ym_constructive_qft_eml
result = analyze_ym_constructive_qft_eml()
print(json.dumps(result, indent=2, default=str))
