"""Session 351 — ECL Normalization Lemma"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.ecl_normalization_lemma_eml import analyze_ecl_normalization_lemma_eml
result = analyze_ecl_normalization_lemma_eml()
print(json.dumps(result, indent=2, default=str))
