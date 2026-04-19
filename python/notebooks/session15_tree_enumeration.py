"""Session 15 — Complex EML Tree Enumeration N<=5: Catalan counts, shape sampling & collapses."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.tree_enumeration_eml import run_session15
print(json.dumps(run_session15(), indent=2, default=str))
