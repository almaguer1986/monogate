import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.friendship_decay_eml import analyze_friendship_decay_eml
result = analyze_friendship_decay_eml()
print(json.dumps(result, indent=2, default=str))