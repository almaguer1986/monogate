"""Session 23 — Bessel Functions in Complex EML."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.bessel_eml import run_session23
print(json.dumps(run_session23(), indent=2, default=str))
