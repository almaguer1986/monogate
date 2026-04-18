"""Session 160 — EML Atlas (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.eml_atlas_eml import analyze_eml_atlas_eml
print(json.dumps(analyze_eml_atlas_eml(), indent=2, default=str))
