"""Session 397 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_hodge_template_eml import analyze_rdl_hodge_template_eml
result = analyze_rdl_hodge_template_eml()
print(json.dumps(result, indent=2, default=str))
