"""Session 124 — graph deep EML (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.graph_deep_eml import analyze_graph_deep_eml
print(json.dumps(analyze_graph_deep_eml(), indent=2, default=str))
