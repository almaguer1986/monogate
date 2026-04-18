import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.humor_punchline_eml import analyze_humor_punchline_eml
result = analyze_humor_punchline_eml()
print(json.dumps(result, indent=2, default=str))
