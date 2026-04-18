import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.zhang_higher_gz_eml import analyze_zhang_higher_gz_eml
result = analyze_zhang_higher_gz_eml()
print(json.dumps(result, indent=2))
