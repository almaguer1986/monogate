"""Session 514 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ocean_currents_thermohaline_eml import analyze_ocean_currents_thermohaline_eml
print(json.dumps(analyze_ocean_currents_thermohaline_eml(), indent=2, default=str))
