import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.biological_signaling_cell_eml import analyze_biological_signaling_cell_eml
result = analyze_biological_signaling_cell_eml()
print(json.dumps(result, indent=2, default=str))
