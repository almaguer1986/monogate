import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.extraction_cost_eml import run_session36
result = run_session36()
print(json.dumps(result, indent=2, default=str))
