import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_l_function_rank_eml import analyze_bsd_l_function_rank_eml
result = analyze_bsd_l_function_rank_eml()
with open(f'python/results/session357_bsd_l_function_rank_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 357 OK')
