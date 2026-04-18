import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_shadow_gap_analysis_eml import analyze_hodge_shadow_gap_analysis_eml
result = analyze_hodge_shadow_gap_analysis_eml()
print(json.dumps(result, indent=2, default=str))
