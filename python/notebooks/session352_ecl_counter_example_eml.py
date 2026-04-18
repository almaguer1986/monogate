"""Session 352 — ECL Counter-Example Hunt"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_counter_example_eml import analyze_ecl_counter_example_eml
result = analyze_ecl_counter_example_eml()
print(json.dumps(result, indent=2, default=str))
