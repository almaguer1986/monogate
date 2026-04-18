import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.tokens_discrete_eml import analyze_tokens_discrete_eml
result = analyze_tokens_discrete_eml()
print(json.dumps(result, indent=2, default=str))
