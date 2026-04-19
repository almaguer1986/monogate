"""Session 14 — Complex BEST Router: route expressions to minimal ceml form."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.complex_best_router_eml import run_session14
print(json.dumps(run_session14(), indent=2, default=str))
