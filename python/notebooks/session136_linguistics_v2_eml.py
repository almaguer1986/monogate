"""Session 136 — Linguistics Deep II: Compositionality, Ambiguity & Semantic Shift (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.linguistics_v2_eml import analyze_linguistics_v2_eml
print(json.dumps(analyze_linguistics_v2_eml(), indent=2, default=str))
