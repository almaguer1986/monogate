"""Session 177 — Topological Phases & Anyons Deep: Topological QC & Braiding Depth Changes (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.anyons_v2_eml import analyze_anyons_v2_eml
print(json.dumps(analyze_anyons_v2_eml(), indent=2, default=str))
