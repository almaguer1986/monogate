"""Session 119 — Transformer Architecture: EML Dissection (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.transformer_eml import analyze_transformer_eml
print(json.dumps(analyze_transformer_eml(), indent=2, default=str))
