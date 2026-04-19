import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.theory_paper_draft_eml import run_session42
result = run_session42()
print(json.dumps(result, indent=2, default=str))
