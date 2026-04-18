"""Session 457 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.eml_formal_theory_eml import analyze_eml_formal_theory_eml
print(json.dumps(analyze_eml_formal_theory_eml(), indent=2, default=str))
