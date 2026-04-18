"""Session 500 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.turbulence_kolmogorov_eml import analyze_turbulence_kolmogorov_eml
print(json.dumps(analyze_turbulence_kolmogorov_eml(), indent=2, default=str))
