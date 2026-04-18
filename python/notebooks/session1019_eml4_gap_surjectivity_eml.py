import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.eml4_gap_surjectivity_eml import analyze_eml4_gap_surjectivity_eml
result = analyze_eml4_gap_surjectivity_eml()
print(json.dumps(result, indent=2))
