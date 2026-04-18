import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.sense_of_self_eml2_eml import analyze_sense_of_self_eml2_eml
result = analyze_sense_of_self_eml2_eml()
print(json.dumps(result, indent=2, default=str))
