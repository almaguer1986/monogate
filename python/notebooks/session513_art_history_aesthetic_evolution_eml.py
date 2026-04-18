"""Session 513 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.art_history_aesthetic_evolution_eml import analyze_art_history_aesthetic_evolution_eml
print(json.dumps(analyze_art_history_aesthetic_evolution_eml(), indent=2, default=str))
