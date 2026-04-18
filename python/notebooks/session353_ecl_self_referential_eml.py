"""Session 353 — ECL Self-Referential"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_self_referential_eml import analyze_ecl_self_referential_eml
result = analyze_ecl_self_referential_eml()
print(json.dumps(result, indent=2, default=str))
