import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecalle_resurgence_eml import run_session41
result = run_session41()
print(json.dumps(result, indent=2, default=str))
