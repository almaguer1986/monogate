import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.hodge_bsd_transfer_eml import analyze_hodge_bsd_transfer_eml
result = analyze_hodge_bsd_transfer_eml()
print(json.dumps(result, indent=2))
