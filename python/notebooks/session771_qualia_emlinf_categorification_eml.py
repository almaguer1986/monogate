import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.qualia_emlinf_categorification_eml import analyze_qualia_emlinf_categorification_eml
result = analyze_qualia_emlinf_categorification_eml()
print(json.dumps(result, indent=2, default=str))
