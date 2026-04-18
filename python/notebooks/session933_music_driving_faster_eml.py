import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.music_driving_faster_eml import analyze_music_driving_faster_eml
result = analyze_music_driving_faster_eml()
print(json.dumps(result, indent=2, default=str))