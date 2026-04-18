import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.beekeeping_swarm_intelligence_eml import analyze_beekeeping_swarm_intelligence_eml
result = analyze_beekeeping_swarm_intelligence_eml()
print(json.dumps(result, indent=2, default=str))
