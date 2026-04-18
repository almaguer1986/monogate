import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.cultural_memes_viral_eml import analyze_cultural_memes_viral_eml
result = analyze_cultural_memes_viral_eml()
print(json.dumps(result, indent=2, default=str))
