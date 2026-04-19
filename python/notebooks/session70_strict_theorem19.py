"""S70 — i-Constructibility: strict theorem19"""
import subprocess, sys
from pathlib import Path
result = subprocess.run(
    [sys.executable, "python/experiments/i_strict_s70.py"],
    cwd=Path(__file__).parent.parent.parent,
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr, file=sys.stderr)
