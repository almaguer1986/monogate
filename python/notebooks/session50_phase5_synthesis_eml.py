import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.phase5_synthesis_eml import run_session50
result = run_session50()
print(json.dumps(result, indent=2, default=str))
