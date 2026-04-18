import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hybrid_human_ai_eml import analyze_hybrid_human_ai_eml
result = analyze_hybrid_human_ai_eml()
print(json.dumps(result, indent=2, default=str))