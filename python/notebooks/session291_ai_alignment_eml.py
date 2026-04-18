import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.ai_alignment_eml import analyze_ai_alignment_eml
result = analyze_ai_alignment_eml()
print(json.dumps(result, indent=2, default=str))
