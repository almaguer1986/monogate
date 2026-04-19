"""Session 8 — PySR Benchmark: EML vs PySR on Nguyen-1 through Nguyen-10."""
import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from monogate.frontiers.pysr_benchmark_eml import run_session8
print(json.dumps(run_session8(), indent=2, default=str))
