"""Session 520 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.love_attachment_theory_eml import analyze_love_attachment_theory_eml
print(json.dumps(analyze_love_attachment_theory_eml(), indent=2, default=str))
