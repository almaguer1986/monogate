import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.dsp_primitives_eml import run_session44
result = run_session44()
print(json.dumps(result, indent=2, default=str))
