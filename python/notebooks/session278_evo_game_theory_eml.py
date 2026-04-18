import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.evo_game_theory_eml import analyze_evo_game_theory_eml
result = analyze_evo_game_theory_eml()
print(json.dumps(result, indent=2, default=str))
