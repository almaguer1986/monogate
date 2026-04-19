"""Session 21 — Hyperbolic Function Complexity."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.hyperbolic_complexity_eml import run_session21
print(json.dumps(run_session21(), indent=2, default=str))
