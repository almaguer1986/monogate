import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.quantum_wavefunctions_eml import run_session46
result = run_session46()
print(json.dumps(result, indent=2, default=str))
