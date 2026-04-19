"""S77 — i-Constructibility: challenge board"""
import subprocess, sys
from pathlib import Path
result = subprocess.run(
    [sys.executable, "python/experiments/i_challenge_board_s77.py"],
    cwd=Path(__file__).parent.parent.parent,
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr, file=sys.stderr)
