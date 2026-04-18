"""Session 320 — RH-EML Random Matrix Theory"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_rmt_eml import analyze_rh_eml_rmt_eml
result = analyze_rh_eml_rmt_eml()
print(json.dumps(result, indent=2, default=str))
