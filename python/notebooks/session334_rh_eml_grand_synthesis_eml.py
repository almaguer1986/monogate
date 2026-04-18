"""Session 334 — RH-EML Grand Synthesis"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_eml_grand_synthesis_eml import analyze_rh_eml_grand_synthesis_eml
result = analyze_rh_eml_grand_synthesis_eml()
print(json.dumps(result, indent=2, default=str))
