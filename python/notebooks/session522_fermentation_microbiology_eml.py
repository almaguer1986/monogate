"""Session 522 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.fermentation_microbiology_eml import analyze_fermentation_microbiology_eml
print(json.dumps(analyze_fermentation_microbiology_eml(), indent=2, default=str))
