import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.biofield_aura_eml import analyze_biofield_aura_eml
result = analyze_biofield_aura_eml()
print(json.dumps(result, indent=2, default=str))
