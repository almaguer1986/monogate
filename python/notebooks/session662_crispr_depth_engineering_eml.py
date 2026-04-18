import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.crispr_depth_engineering_eml import analyze_crispr_depth_engineering_eml
result = analyze_crispr_depth_engineering_eml()
print(json.dumps(result, indent=2, default=str))
