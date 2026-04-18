import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.active_inference_free_energy_implications_eml import analyze_active_inference_free_energy_implications_eml
result = analyze_active_inference_free_energy_implications_eml()
print(json.dumps(result, indent=2, default=str))
