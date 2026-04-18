"""Session 459 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.explicit_eml3_zeta_rep_eml import analyze_explicit_eml3_zeta_rep_eml
print(json.dumps(analyze_explicit_eml3_zeta_rep_eml(), indent=2, default=str))
