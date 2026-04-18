"""Session 496 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.active_inference_free_energy_eml import analyze_active_inference_free_energy_eml
print(json.dumps(analyze_active_inference_free_energy_eml(), indent=2, default=str))
