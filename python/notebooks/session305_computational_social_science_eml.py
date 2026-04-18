"""Session 305 — Computational Social Science"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.computational_social_science_eml import analyze_computational_social_science_eml
result = analyze_computational_social_science_eml()
print(json.dumps(result, indent=2, default=str))
