"""Session 395 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_referee_response_eml import analyze_rdl_referee_response_eml
result = analyze_rdl_referee_response_eml()
print(json.dumps(result, indent=2, default=str))
