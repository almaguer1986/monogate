"""Session 300 — High-Energy Astrophysics"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.high_energy_astrophysics_eml import analyze_high_energy_astrophysics_eml
result = analyze_high_energy_astrophysics_eml()
print(json.dumps(result, indent=2, default=str))
