import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.stuttering_trapped_oscillation_eml import analyze_stuttering_trapped_oscillation_eml
result = analyze_stuttering_trapped_oscillation_eml()
print(json.dumps(result, indent=2, default=str))
