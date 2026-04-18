"""Session 166 — notebook script"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.protein_folding_eml import analyze_protein_folding_eml
print(json.dumps(analyze_protein_folding_eml(), indent=2, default=str))
