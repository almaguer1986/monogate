"""Session 187 — Topological Phases Deep II: Anyonic Statistics, TQC & Braiding Depth Changes (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.anyons_v3_eml import analyze_anyons_v3_eml
print(json.dumps(analyze_anyons_v3_eml(), indent=2, default=str))
