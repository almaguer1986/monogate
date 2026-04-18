"""Session 402 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_zero_spacing_eml import analyze_rdl_zero_spacing_eml
result = analyze_rdl_zero_spacing_eml()
print(json.dumps(result, indent=2, default=str))
