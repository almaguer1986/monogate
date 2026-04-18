"""Session 494 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.music_cognition_neural_eml import analyze_music_cognition_neural_eml
print(json.dumps(analyze_music_cognition_neural_eml(), indent=2, default=str))
