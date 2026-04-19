import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.sin_barrier_revisited_eml import run_session39
result = run_session39()
print(json.dumps(result, indent=2, default=str))
