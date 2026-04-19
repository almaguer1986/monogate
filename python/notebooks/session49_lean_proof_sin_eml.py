import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.lean_proof_sin_eml import run_session49
result = run_session49()
print(json.dumps(result, indent=2, default=str))
