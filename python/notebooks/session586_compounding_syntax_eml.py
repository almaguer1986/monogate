import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.compounding_syntax_eml import analyze_compounding_syntax_eml
result = analyze_compounding_syntax_eml()
print(json.dumps(result, indent=2, default=str))
