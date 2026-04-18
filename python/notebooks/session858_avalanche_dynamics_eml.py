import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.avalanche_dynamics_eml import analyze_avalanche_dynamics_eml
result = analyze_avalanche_dynamics_eml()
print(json.dumps(result, indent=2, default=str))