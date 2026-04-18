import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.strata_game_fidelity_v2_eml import analyze_strata_game_fidelity_v2_eml
result = analyze_strata_game_fidelity_v2_eml()
print(json.dumps(result, indent=2, default=str))
