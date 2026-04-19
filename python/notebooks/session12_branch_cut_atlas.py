"""Session 12 — Complex EML Branch Cut Atlas: singularities, monodromy & safe domains."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.branch_cut_atlas_eml import run_session12
print(json.dumps(run_session12(), indent=2, default=str))
