import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.birdsong_dialects_eml import analyze_birdsong_dialects_eml
result = analyze_birdsong_dialects_eml()
print(json.dumps(result, indent=2, default=str))