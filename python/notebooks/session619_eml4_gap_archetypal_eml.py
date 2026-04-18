import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.eml4_gap_archetypal_eml import analyze_eml4_gap_archetypal_eml
result = analyze_eml4_gap_archetypal_eml()
print(json.dumps(result, indent=2, default=str))
