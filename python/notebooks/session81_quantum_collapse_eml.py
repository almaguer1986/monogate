"""Session 81 — Quantum Randomness: Collapse & Decoherence (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.quantum_collapse_eml import analyze_quantum_collapse_eml
print(json.dumps(analyze_quantum_collapse_eml(), indent=2, default=str))
