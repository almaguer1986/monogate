import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.altered_states_emlinf_threshold_eml import analyze_altered_states_emlinf_threshold_eml
result = analyze_altered_states_emlinf_threshold_eml()
print(json.dumps(result, indent=2, default=str))
