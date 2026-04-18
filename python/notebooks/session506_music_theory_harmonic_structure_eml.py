"""Session 506 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.music_theory_harmonic_structure_eml import analyze_music_theory_harmonic_structure_eml
print(json.dumps(analyze_music_theory_harmonic_structure_eml(), indent=2, default=str))
