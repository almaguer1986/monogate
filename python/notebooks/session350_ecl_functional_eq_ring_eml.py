"""Session 350 — ECL Functional Eq Ring"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_functional_eq_ring_eml import analyze_ecl_functional_eq_ring_eml
result = analyze_ecl_functional_eq_ring_eml()
print(json.dumps(result, indent=2, default=str))
