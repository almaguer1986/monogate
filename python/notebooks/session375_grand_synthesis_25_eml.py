import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.grand_synthesis_25_eml import analyze_grand_synthesis_25_eml
result = analyze_grand_synthesis_25_eml()
with open(f'python/results/session375_grand_synthesis_25_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 375 OK')
