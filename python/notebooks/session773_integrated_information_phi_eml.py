import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.integrated_information_phi_eml import analyze_integrated_information_phi_eml
result = analyze_integrated_information_phi_eml()
print(json.dumps(result, indent=2, default=str))
