"""Session 106 — Linguistics & Semantics (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.linguistics_eml import analyze_linguistics_eml
print(json.dumps(analyze_linguistics_eml(), indent=2, default=str))
