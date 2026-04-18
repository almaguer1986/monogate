import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_langlands_higher_rank_eml import analyze_bsd_langlands_higher_rank_eml
result = analyze_bsd_langlands_higher_rank_eml()
print(json.dumps(result, indent=2, default=str))
