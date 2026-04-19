import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.depth_hierarchy_strictness_eml import run_session37
result = run_session37()
print(json.dumps(result, indent=2, default=str))
