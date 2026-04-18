"""Session 338 — Paleontology Extinctions"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.paleontology_extinction_eml import analyze_paleontology_extinction_eml
result = analyze_paleontology_extinction_eml()
print(json.dumps(result, indent=2, default=str))
