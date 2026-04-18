import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_shadow_refinement_eml import analyze_bsd_shadow_refinement_eml
result = analyze_bsd_shadow_refinement_eml()
with open(f'python/results/session361_bsd_shadow_refinement_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 361 OK')
