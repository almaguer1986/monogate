"""Session 511 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.competitive_game_theory_eml import analyze_competitive_game_theory_eml
print(json.dumps(analyze_competitive_game_theory_eml(), indent=2, default=str))
