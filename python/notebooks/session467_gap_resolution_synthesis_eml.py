"""Session 467 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.gap_resolution_synthesis_eml import analyze_gap_resolution_synthesis_eml
print(json.dumps(analyze_gap_resolution_synthesis_eml(), indent=2, default=str))
