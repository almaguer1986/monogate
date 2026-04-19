import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.cvnn_benchmark_eml import run_session45
result = run_session45()
print(json.dumps(result, indent=2, default=str))
