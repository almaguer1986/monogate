import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.completeness_theorem_eml import run_session35
result = run_session35()
print(json.dumps(result, indent=2, default=str))
