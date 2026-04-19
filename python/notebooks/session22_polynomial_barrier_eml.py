"""Session 22 — Polynomial Barrier in Complex EML."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.polynomial_barrier_eml import run_session22
print(json.dumps(run_session22(), indent=2, default=str))
