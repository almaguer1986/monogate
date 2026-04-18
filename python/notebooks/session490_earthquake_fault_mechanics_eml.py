"""Session 490 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.earthquake_fault_mechanics_eml import analyze_earthquake_fault_mechanics_eml
print(json.dumps(analyze_earthquake_fault_mechanics_eml(), indent=2, default=str))
