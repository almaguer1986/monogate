"""Session 155 — QFT Non-Perturbative (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.qft_nonpert_eml import analyze_qft_nonpert_eml
print(json.dumps(analyze_qft_nonpert_eml(), indent=2, default=str))
