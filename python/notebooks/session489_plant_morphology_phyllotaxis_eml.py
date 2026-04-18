"""Session 489 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.plant_morphology_phyllotaxis_eml import analyze_plant_morphology_phyllotaxis_eml
print(json.dumps(analyze_plant_morphology_phyllotaxis_eml(), indent=2, default=str))
