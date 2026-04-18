import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.phantom_limb_pain_eml import analyze_phantom_limb_pain_eml
result = analyze_phantom_limb_pain_eml()
print(json.dumps(result, indent=2, default=str))