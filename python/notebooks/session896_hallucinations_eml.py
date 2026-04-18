import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hallucinations_eml import analyze_hallucinations_eml
result = analyze_hallucinations_eml()
print(json.dumps(result, indent=2, default=str))