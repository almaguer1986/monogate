"""Session 495 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.meta_exploration_atlas_dynamics_eml import analyze_meta_exploration_atlas_dynamics_eml
print(json.dumps(analyze_meta_exploration_atlas_dynamics_eml(), indent=2, default=str))
