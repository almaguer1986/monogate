"""Session 380 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_shadow_enforcement_eml import analyze_rdl_shadow_enforcement_eml
result = analyze_rdl_shadow_enforcement_eml()
print(json.dumps(result, indent=2, default=str))
