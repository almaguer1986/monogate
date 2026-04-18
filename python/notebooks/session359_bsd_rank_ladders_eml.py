import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_rank_ladders_eml import analyze_bsd_rank_ladders_eml
result = analyze_bsd_rank_ladders_eml()
with open(f'python/results/session359_bsd_rank_ladders_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 359 OK')
