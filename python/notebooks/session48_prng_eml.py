import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.prng_eml import run_session48
result = run_session48()
print(json.dumps(result, indent=2, default=str))
