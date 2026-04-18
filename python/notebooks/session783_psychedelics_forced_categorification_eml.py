import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.psychedelics_forced_categorification_eml import analyze_psychedelics_forced_categorification_eml
result = analyze_psychedelics_forced_categorification_eml()
print(json.dumps(result, indent=2, default=str))
