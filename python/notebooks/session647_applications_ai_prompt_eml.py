import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.applications_ai_prompt_eml import analyze_applications_ai_prompt_eml
result = analyze_applications_ai_prompt_eml()
print(json.dumps(result, indent=2, default=str))
