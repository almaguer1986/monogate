"""Session 183 — Music & Perception Deep III: Timbre, Emotion & EML-∞ Strata (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.music_perception_v2_eml import analyze_music_perception_v2_eml
print(json.dumps(analyze_music_perception_v2_eml(), indent=2, default=str))
