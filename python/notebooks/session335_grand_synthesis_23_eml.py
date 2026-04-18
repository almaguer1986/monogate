"""Session 335 — Grand Synthesis XXIII"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.grand_synthesis_23_eml import analyze_grand_synthesis_23_eml
result = analyze_grand_synthesis_23_eml()
print(json.dumps(result, indent=2, default=str))
