import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.voice_recognition_eml import analyze_voice_recognition_eml
result = analyze_voice_recognition_eml()
print(json.dumps(result, indent=2, default=str))