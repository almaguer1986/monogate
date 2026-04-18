"""Session 341 — HFT Microstructure"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.hft_microstructure_eml import analyze_hft_microstructure_eml
result = analyze_hft_microstructure_eml()
print(json.dumps(result, indent=2, default=str))
