import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.connectomics_neural_dynamics_eml import analyze_connectomics_neural_dynamics_eml
result = analyze_connectomics_neural_dynamics_eml()
print(json.dumps(result, indent=2, default=str))
