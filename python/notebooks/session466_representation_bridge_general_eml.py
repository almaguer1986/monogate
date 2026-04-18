"""Session 466 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.representation_bridge_general_eml import analyze_representation_bridge_general_eml
print(json.dumps(analyze_representation_bridge_general_eml(), indent=2, default=str))
