"""Session 509 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.dreams_sleep_architecture_eml import analyze_dreams_sleep_architecture_eml
print(json.dumps(analyze_dreams_sleep_architecture_eml(), indent=2, default=str))
