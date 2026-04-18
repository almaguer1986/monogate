import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_langlands_v2_eml import analyze_bsd_langlands_v2_eml
result = analyze_bsd_langlands_v2_eml()
print(json.dumps(result, indent=2, default=str))