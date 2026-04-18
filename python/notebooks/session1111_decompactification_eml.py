import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.decompactification_eml import analyze_decompactification_eml
result = analyze_decompactification_eml()
print(json.dumps(result, indent=2))
