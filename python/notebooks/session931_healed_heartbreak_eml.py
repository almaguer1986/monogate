import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.healed_heartbreak_eml import analyze_healed_heartbreak_eml
result = analyze_healed_heartbreak_eml()
print(json.dumps(result, indent=2, default=str))