import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.ym_phase1_synthesis_eml import analyze_ym_phase1_synthesis_eml
result = analyze_ym_phase1_synthesis_eml()
print(json.dumps(result, indent=2))
