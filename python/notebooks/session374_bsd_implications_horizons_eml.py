import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_implications_horizons_eml import analyze_bsd_implications_horizons_eml
result = analyze_bsd_implications_horizons_eml()
with open(f'python/results/session374_bsd_implications_horizons_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 374 OK')
