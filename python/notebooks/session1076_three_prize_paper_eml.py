import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.three_prize_paper_eml import analyze_three_prize_paper_eml
result = analyze_three_prize_paper_eml()
print(json.dumps(result, indent=2))
