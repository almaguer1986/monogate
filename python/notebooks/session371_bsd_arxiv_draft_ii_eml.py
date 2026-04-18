import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_arxiv_draft_ii_eml import analyze_bsd_arxiv_draft_ii_eml
result = analyze_bsd_arxiv_draft_ii_eml()
with open(f'python/results/session371_bsd_arxiv_draft_ii_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 371 OK')
