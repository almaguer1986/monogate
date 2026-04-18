import json, sys
sys.path.insert(0, 'D:/monogate/python')
from monogate.frontiers.ring_depth_qft_eml import analyze_ring_depth_qft_eml
result = analyze_ring_depth_qft_eml()
print(json.dumps(result, indent=2, default=str))
