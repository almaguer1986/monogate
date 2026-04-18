import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.grief_stages_loss_eml import analyze_grief_stages_loss_eml
result = analyze_grief_stages_loss_eml()
print(json.dumps(result, indent=2, default=str))
