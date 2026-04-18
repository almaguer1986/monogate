import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.edge_case_counterexample_eml import analyze_edge_case_counterexample_eml
result = analyze_edge_case_counterexample_eml()
print(json.dumps(result, indent=2, default=str))
