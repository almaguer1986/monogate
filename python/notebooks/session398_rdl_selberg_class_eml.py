"""Session 398 notebook"""
import json, sys
sys.path.insert(0, "python")
from monogate.frontiers.rdl_selberg_class_eml import analyze_rdl_selberg_class_eml
result = analyze_rdl_selberg_class_eml()
print(json.dumps(result, indent=2, default=str))
