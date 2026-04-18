"""Session 484 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.lean_sorry_eml4_gap_structural_eml import analyze_lean_sorry_eml4_gap_structural_eml
print(json.dumps(analyze_lean_sorry_eml4_gap_structural_eml(), indent=2, default=str))
