import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.five_prizes_rank_eml import analyze_five_prizes_rank_eml
result = analyze_five_prizes_rank_eml()
print(json.dumps(result, indent=2))
