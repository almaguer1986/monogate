import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.black_hole_holographic_eml import analyze_black_hole_holographic_eml
result = analyze_black_hole_holographic_eml()
print(json.dumps(result, indent=2, default=str))
