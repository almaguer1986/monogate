import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.contagious_yawning_eml import analyze_contagious_yawning_eml
result = analyze_contagious_yawning_eml()
print(json.dumps(result, indent=2, default=str))