import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.langlands_remaining_problems_eml import analyze_langlands_remaining_problems_eml
result = analyze_langlands_remaining_problems_eml()
print(json.dumps(result, indent=2, default=str))