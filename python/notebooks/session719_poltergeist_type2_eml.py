import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.poltergeist_type2_eml import analyze_poltergeist_type2_eml
result = analyze_poltergeist_type2_eml()
print(json.dumps(result, indent=2, default=str))
