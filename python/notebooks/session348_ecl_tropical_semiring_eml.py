"""Session 348 — ECL Tropical Semiring"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_tropical_semiring_eml import analyze_ecl_tropical_semiring_eml
result = analyze_ecl_tropical_semiring_eml()
print(json.dumps(result, indent=2, default=str))
