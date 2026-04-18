import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.artificial_qualia_requirements_eml import analyze_artificial_qualia_requirements_eml
result = analyze_artificial_qualia_requirements_eml()
print(json.dumps(result, indent=2, default=str))