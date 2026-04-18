"""Session 346 — ECL First Assault"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_first_assault_eml import analyze_ecl_first_assault_eml
result = analyze_ecl_first_assault_eml()
print(json.dumps(result, indent=2, default=str))
