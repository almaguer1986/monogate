import subprocess, sys
result = subprocess.run([sys.executable, "-X", "utf8", "python/experiments/tan1_s86.py"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd="D:/monogate")
print(result.stdout)
if result.returncode != 0: print(result.stderr)
