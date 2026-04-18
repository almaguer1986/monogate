import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.sha_finiteness_parallel_eml import analyze_sha_finiteness_parallel_eml
result = analyze_sha_finiteness_parallel_eml()
print(json.dumps(result, indent=2))
