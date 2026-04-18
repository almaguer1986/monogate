"""Session 507 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.cooking_flavor_chemistry_eml import analyze_cooking_flavor_chemistry_eml
print(json.dumps(analyze_cooking_flavor_chemistry_eml(), indent=2, default=str))
