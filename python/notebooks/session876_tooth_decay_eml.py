import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tooth_decay_eml import analyze_tooth_decay_eml
result = analyze_tooth_decay_eml()
print(json.dumps(result, indent=2, default=str))