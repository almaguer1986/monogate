import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.analytic_continuation_conjecture_eml import run_session38
result = run_session38()
print(json.dumps(result, indent=2, default=str))
