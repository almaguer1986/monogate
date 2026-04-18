"""Session 325 — RH-EML Critical Line"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_critical_line_eml import analyze_rh_eml_critical_line_eml
result = analyze_rh_eml_critical_line_eml()
print(json.dumps(result, indent=2, default=str))
