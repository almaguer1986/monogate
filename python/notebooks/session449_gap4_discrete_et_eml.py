"""Session 449 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.gap4_discrete_et_eml import analyze_gap4_discrete_et_eml
print(json.dumps(analyze_gap4_discrete_et_eml(), indent=2, default=str))
