import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.quantum_info_shadow_eml import analyze_quantum_info_shadow_eml
print(json.dumps(analyze_quantum_info_shadow_eml(), indent=2, default=str))
