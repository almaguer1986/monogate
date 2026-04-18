"""Session 399 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_zero_density_eml import analyze_rdl_zero_density_eml
result = analyze_rdl_zero_density_eml()
print(json.dumps(result, indent=2, default=str))
