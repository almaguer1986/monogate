"""S62 — i-Constructibility: The Loophole"""
import subprocess, sys
from pathlib import Path

result = subprocess.run(
    [sys.executable, "python/experiments/i_constructibility_s62.py"],
    cwd=Path(__file__).parent.parent.parent,
    capture_output=True, text=True, encoding="utf-8"
)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr, file=sys.stderr)
