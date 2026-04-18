"""Session 108 — Materials Science & Condensed Matter (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.materials_eml import analyze_materials_eml
print(json.dumps(analyze_materials_eml(), indent=2, default=str))
