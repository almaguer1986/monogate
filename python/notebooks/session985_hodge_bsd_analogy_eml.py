import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_bsd_analogy_eml import analyze_hodge_bsd_analogy_eml
result = analyze_hodge_bsd_analogy_eml()
print(json.dumps(result, indent=2, default=str))