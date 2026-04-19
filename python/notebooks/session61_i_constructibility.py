"""S61 — i-Constructibility: Setup and Attack"""
import subprocess, sys, json
from pathlib import Path

result = subprocess.run(
    [sys.executable, "python/experiments/i_constructibility.py"],
    cwd=Path(__file__).parent.parent.parent,
    capture_output=True, text=True, encoding="utf-8"
)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr, file=sys.stderr)
