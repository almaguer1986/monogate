import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hodge_motivic_lf_deep_eml import analyze_hodge_motivic_lf_deep_eml
result = analyze_hodge_motivic_lf_deep_eml()
print(json.dumps(result, indent=2, default=str))
