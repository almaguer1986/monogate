import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.theorem_count_milestone_eml import analyze_theorem_count_milestone_eml
result = analyze_theorem_count_milestone_eml()
print(json.dumps(result, indent=2))
