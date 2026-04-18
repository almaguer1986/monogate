"""Session 505 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.grand_synthesis_30_eml import analyze_grand_synthesis_30_eml
print(json.dumps(analyze_grand_synthesis_30_eml(), indent=2, default=str))
