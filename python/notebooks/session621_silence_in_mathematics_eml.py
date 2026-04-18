import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.silence_in_mathematics_eml import analyze_silence_in_mathematics_eml
result = analyze_silence_in_mathematics_eml()
print(json.dumps(result, indent=2, default=str))
