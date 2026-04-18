import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_surjectivity_gap_eml import analyze_hodge_surjectivity_gap_eml
result = analyze_hodge_surjectivity_gap_eml()
print(json.dumps(result, indent=2, default=str))