import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.ai_next_horizons_eml import analyze_ai_next_horizons_eml
result = analyze_ai_next_horizons_eml()
print(json.dumps(result, indent=2, default=str))