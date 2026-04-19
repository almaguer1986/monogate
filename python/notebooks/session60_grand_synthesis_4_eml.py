import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.grand_synthesis_4_eml import run_session60
result = run_session60()
print(json.dumps(result, indent=2, default=str))
