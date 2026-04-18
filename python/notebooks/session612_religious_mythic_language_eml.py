import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.religious_mythic_language_eml import analyze_religious_mythic_language_eml
result = analyze_religious_mythic_language_eml()
print(json.dumps(result, indent=2, default=str))
