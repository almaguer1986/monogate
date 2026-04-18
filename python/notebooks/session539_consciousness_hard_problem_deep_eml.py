import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.consciousness_hard_problem_deep_eml import analyze_consciousness_hard_problem_deep_eml
result = analyze_consciousness_hard_problem_deep_eml()
print(json.dumps(result, indent=2, default=str))
