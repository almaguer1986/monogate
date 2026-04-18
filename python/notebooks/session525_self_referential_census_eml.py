"""Session 525 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.self_referential_census_eml import analyze_self_referential_census_eml
print(json.dumps(analyze_self_referential_census_eml(), indent=2, default=str))
