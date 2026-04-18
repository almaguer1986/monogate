import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.rl_reward_eml import analyze_rl_reward_eml
result = analyze_rl_reward_eml()
print(json.dumps(result, indent=2, default=str))