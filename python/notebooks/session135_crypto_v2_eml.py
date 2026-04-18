"""Session 135 — Cryptography Deep II: One-Way Functions, Lattices & Zero-Knowledge (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.crypto_v2_eml import analyze_crypto_v2_eml
print(json.dumps(analyze_crypto_v2_eml(), indent=2, default=str))
