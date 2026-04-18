"""Session 394 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_implications_horizons_eml import analyze_rdl_implications_horizons_eml
result = analyze_rdl_implications_horizons_eml()
print(json.dumps(result, indent=2, default=str))
