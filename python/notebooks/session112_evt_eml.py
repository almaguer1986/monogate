"""Session 112 — Extreme Value Theory & Rare Events (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.evt_eml import analyze_evt_eml
print(json.dumps(analyze_evt_eml(), indent=2, default=str))
