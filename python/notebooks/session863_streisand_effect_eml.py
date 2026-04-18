import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.streisand_effect_eml import analyze_streisand_effect_eml
result = analyze_streisand_effect_eml()
print(json.dumps(result, indent=2, default=str))