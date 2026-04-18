"""Session 307 — Semiring Self-Geometry"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.semiring_self_geometry_eml import analyze_semiring_self_geometry_eml
result = analyze_semiring_self_geometry_eml()
print(json.dumps(result, indent=2, default=str))
