import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.selmer_general_rank_eml import analyze_selmer_general_rank_eml
result = analyze_selmer_general_rank_eml()
print(json.dumps(result, indent=2))
