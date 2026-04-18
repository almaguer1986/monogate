"""Session 517 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.poetry_meter_eml import analyze_poetry_meter_eml
print(json.dumps(analyze_poetry_meter_eml(), indent=2, default=str))
