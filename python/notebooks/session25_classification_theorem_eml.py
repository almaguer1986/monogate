"""Session 25 — Complex EML Classification Theorem."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.classification_theorem_eml import run_session25
print(json.dumps(run_session25(), indent=2, default=str))
