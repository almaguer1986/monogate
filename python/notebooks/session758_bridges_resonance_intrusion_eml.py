import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bridges_resonance_intrusion_eml import analyze_bridges_resonance_intrusion_eml
result = analyze_bridges_resonance_intrusion_eml()
print(json.dumps(result, indent=2, default=str))
