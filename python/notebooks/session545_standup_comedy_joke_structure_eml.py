import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.standup_comedy_joke_structure_eml import analyze_standup_comedy_joke_structure_eml
result = analyze_standup_comedy_joke_structure_eml()
print(json.dumps(result, indent=2, default=str))
