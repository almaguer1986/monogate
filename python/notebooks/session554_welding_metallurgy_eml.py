import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.welding_metallurgy_eml import analyze_welding_metallurgy_eml
result = analyze_welding_metallurgy_eml()
print(json.dumps(result, indent=2, default=str))
