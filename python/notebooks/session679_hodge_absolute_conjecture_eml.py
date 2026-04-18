import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_absolute_conjecture_eml import analyze_hodge_absolute_conjecture_eml
result = analyze_hodge_absolute_conjecture_eml()
print(json.dumps(result, indent=2, default=str))
