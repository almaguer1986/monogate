import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.scientific_communication_eml import analyze_scientific_communication_eml
result = analyze_scientific_communication_eml()
print(json.dumps(result, indent=2, default=str))
