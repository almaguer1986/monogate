"""Session 20 — Trig Collapse Theorem."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.trig_collapse_theorem_eml import run_session20
print(json.dumps(run_session20(), indent=2, default=str))
