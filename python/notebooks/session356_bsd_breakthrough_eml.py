import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_breakthrough_eml import analyze_bsd_breakthrough_eml
result = analyze_bsd_breakthrough_eml()
with open(f'python/results/session356_bsd_breakthrough_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 356 OK')
