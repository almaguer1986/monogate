"""Session 486 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.quantum_gravity_lqg_eml import analyze_quantum_gravity_lqg_eml
print(json.dumps(analyze_quantum_gravity_lqg_eml(), indent=2, default=str))
