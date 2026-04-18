"""Session 330 — RH-EML Self-Referential"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_self_referential_eml import analyze_rh_eml_self_referential_eml
result = analyze_rh_eml_self_referential_eml()
print(json.dumps(result, indent=2, default=str))
