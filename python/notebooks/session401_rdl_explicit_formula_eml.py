"""Session 401 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_explicit_formula_eml import analyze_rdl_explicit_formula_eml
result = analyze_rdl_explicit_formula_eml()
print(json.dumps(result, indent=2, default=str))
