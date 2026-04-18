import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.psychoacoustics_deep_eml import analyze_psychoacoustics_deep_eml
result = analyze_psychoacoustics_deep_eml()
print(json.dumps(result, indent=2, default=str))
