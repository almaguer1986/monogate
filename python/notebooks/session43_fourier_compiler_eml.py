import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.fourier_compiler_eml import run_session43
result = run_session43()
print(json.dumps(result, indent=2, default=str))
