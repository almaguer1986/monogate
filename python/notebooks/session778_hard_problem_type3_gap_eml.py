import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.hard_problem_type3_gap_eml import analyze_hard_problem_type3_gap_eml
result = analyze_hard_problem_type3_gap_eml()
print(json.dumps(result, indent=2, default=str))
