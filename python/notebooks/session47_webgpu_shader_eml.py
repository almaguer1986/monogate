import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.webgpu_shader_eml import run_session47
result = run_session47()
print(json.dumps(result, indent=2, default=str))
