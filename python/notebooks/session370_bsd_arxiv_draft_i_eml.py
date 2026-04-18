import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.bsd_arxiv_draft_i_eml import analyze_bsd_arxiv_draft_i_eml
result = analyze_bsd_arxiv_draft_i_eml()
with open(f'python/results/session370_bsd_arxiv_draft_i_eml.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, default=str)
print(f'Session 370 OK')
