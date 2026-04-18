import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ghosts_structured_absence_eml import analyze_ghosts_structured_absence_eml
result = analyze_ghosts_structured_absence_eml()
print(json.dumps(result, indent=2, default=str))
