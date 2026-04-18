"""Session 318 — RH-EML Explicit Formula"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_explicit_formula_eml import analyze_rh_eml_explicit_formula_eml
result = analyze_rh_eml_explicit_formula_eml()
print(json.dumps(result, indent=2, default=str))
