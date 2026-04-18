import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_sha_finiteness_eml import analyze_bsd_sha_finiteness_eml
result = analyze_bsd_sha_finiteness_eml()
print(json.dumps(result, indent=2, default=str))
