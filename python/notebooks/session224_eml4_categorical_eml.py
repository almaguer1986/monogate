"""Session 224 — eml4 categorical eml (notebook script)"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from monogate.frontiers.eml4_categorical_eml import analyze_eml4_categorical_eml
print(json.dumps(analyze_eml4_categorical_eml(), indent=2, default=str))
