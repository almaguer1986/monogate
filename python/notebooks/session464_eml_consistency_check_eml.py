"""Session 464 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.eml_consistency_check_eml import analyze_eml_consistency_check_eml
print(json.dumps(analyze_eml_consistency_check_eml(), indent=2, default=str))
