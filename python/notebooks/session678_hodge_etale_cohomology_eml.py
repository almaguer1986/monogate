import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_etale_cohomology_eml import analyze_hodge_etale_cohomology_eml
result = analyze_hodge_etale_cohomology_eml()
print(json.dumps(result, indent=2, default=str))
