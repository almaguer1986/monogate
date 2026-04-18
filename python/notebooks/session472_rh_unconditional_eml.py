"""Session 472 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.rh_unconditional_eml import analyze_rh_unconditional_eml
print(json.dumps(analyze_rh_unconditional_eml(), indent=2, default=str))
