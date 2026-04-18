"""Session 471 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.tropical_absolute_value_eml import analyze_tropical_absolute_value_eml
print(json.dumps(analyze_tropical_absolute_value_eml(), indent=2, default=str))
