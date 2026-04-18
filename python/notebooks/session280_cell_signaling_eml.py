import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.cell_signaling_eml import analyze_cell_signaling_eml
result = analyze_cell_signaling_eml()
print(json.dumps(result, indent=2, default=str))
