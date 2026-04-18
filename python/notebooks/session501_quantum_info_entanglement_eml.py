"""Session 501 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.quantum_info_entanglement_eml import analyze_quantum_info_entanglement_eml
print(json.dumps(analyze_quantum_info_entanglement_eml(), indent=2, default=str))
