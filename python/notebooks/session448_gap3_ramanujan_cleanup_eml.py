"""Session 448 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.gap3_ramanujan_cleanup_eml import analyze_gap3_ramanujan_cleanup_eml
print(json.dumps(analyze_gap3_ramanujan_cleanup_eml(), indent=2, default=str))
