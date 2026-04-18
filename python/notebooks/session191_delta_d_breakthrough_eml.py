"""Session 191 — Δd Anomaly Breakthrough: The Missing Link (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.delta_d_breakthrough_eml import analyze_delta_d_breakthrough_eml
print(json.dumps(analyze_delta_d_breakthrough_eml(), indent=2, default=str))
