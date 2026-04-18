"""Session 314 — CapCard Next-Gen"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.capcard_next_gen_eml import analyze_capcard_next_gen_eml
result = analyze_capcard_next_gen_eml()
print(json.dumps(result, indent=2, default=str))
