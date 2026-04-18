import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.grand_synthesis_after_consciousness_eml import analyze_grand_synthesis_after_consciousness_eml
result = analyze_grand_synthesis_after_consciousness_eml()
print(json.dumps(result, indent=2, default=str))
