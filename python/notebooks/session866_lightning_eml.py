import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.lightning_eml import analyze_lightning_eml
result = analyze_lightning_eml()
print(json.dumps(result, indent=2, default=str))