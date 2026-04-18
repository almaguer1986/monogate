import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.applications_poetry_eml import analyze_applications_poetry_eml
result = analyze_applications_poetry_eml()
print(json.dumps(result, indent=2, default=str))
