import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.perfect_pitch_eml import analyze_perfect_pitch_eml
result = analyze_perfect_pitch_eml()
print(json.dumps(result, indent=2, default=str))