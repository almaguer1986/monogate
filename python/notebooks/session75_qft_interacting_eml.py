"""Session 75 — QFT Interacting Theories EML (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.qft_interacting_eml import analyze_qft_interacting_eml

result = analyze_qft_interacting_eml()
print(json.dumps(result, indent=2, default=str))
