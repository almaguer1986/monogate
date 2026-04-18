"""Session 85 — NS Deep Dive: BKM Criterion (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.ns_bkm_deep_eml import analyze_ns_bkm_deep_eml
print(json.dumps(analyze_ns_bkm_deep_eml(), indent=2, default=str))
