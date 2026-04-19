"""Session 13 — Real-vs-Complex EML Cost Table: depth collapse for elementary functions."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.cost_table_eml import run_session13
print(json.dumps(run_session13(), indent=2, default=str))
