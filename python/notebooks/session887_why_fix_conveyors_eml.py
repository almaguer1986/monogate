import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.why_fix_conveyors_eml import analyze_why_fix_conveyors_eml
result = analyze_why_fix_conveyors_eml()
print(json.dumps(result, indent=2, default=str))