import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_functional_eq_parity_eml import analyze_bsd_functional_eq_parity_eml
result = analyze_bsd_functional_eq_parity_eml()
with open(f'python/results/session363_bsd_functional_eq_parity_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 363 OK')
