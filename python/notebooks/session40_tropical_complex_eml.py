import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.tropical_complex_eml import run_session40
result = run_session40()
print(json.dumps(result, indent=2, default=str))
