#!/usr/bin/env python3
"""
release_v0.11.0.py — Final release readiness check for monogate v0.11.0.

Runs in order:
  1. Version verification (monogate/__init__.py + pyproject.toml both == 0.11.0)
  2. make reproduce-n11 (N=11 claims, ~30s from cached)
  3. Full test suite (make test)
  4. Paper PDF build (make paper) — skipped if pdflatex not found
  5. Import smoke-test for all major v0.10/v0.11 exports
  6. Prints a final readiness summary

Usage::

    cd python
    python scripts/release_v0.11.0.py

Exit code 0 = all checks passed, ready to tag and push.
Exit code 1 = one or more checks failed.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent   # repo root (monogate/)
PYTHON_DIR = ROOT / "python"

EXPECTED_VERSION = "0.11.0"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def ok(msg: str)   -> None: print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg: str) -> None: print(f"  {RED}[FAIL]{RESET}  {msg}")
def warn(msg: str) -> None: print(f"  {YELLOW}[SKIP]{RESET}  {msg}")
def header(msg: str) -> None:
    print(f"\n{msg}")
    print("─" * len(msg))


checks: list[tuple[str, bool]] = []


def record(label: str, passed: bool) -> bool:
    checks.append((label, passed))
    (ok if passed else fail)(label)
    return passed


# ── 1. Version check ─────────────────────────────────────────────────────────
header("1. Version verification")

init_path = PYTHON_DIR / "monogate" / "__init__.py"
pyproject_path = PYTHON_DIR / "pyproject.toml"

init_version = None
for line in init_path.read_text().splitlines():
    if line.startswith("__version__"):
        init_version = line.split('"')[1]
        break

pyproject_version = None
for line in pyproject_path.read_text().splitlines():
    if line.strip().startswith("version"):
        pyproject_version = line.split('"')[1]
        break

record(f"__init__.py version == {EXPECTED_VERSION}", init_version == EXPECTED_VERSION)
record(f"pyproject.toml version == {EXPECTED_VERSION}", pyproject_version == EXPECTED_VERSION)


# ── 2. N=11 reproducibility ───────────────────────────────────────────────────
header("2. N=11 claim verification (scripts/reproduce_n11.py)")

t0 = time.perf_counter()
result = subprocess.run(
    [sys.executable, str(PYTHON_DIR / "scripts" / "reproduce_n11.py")],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    cwd=str(PYTHON_DIR),
)
elapsed = time.perf_counter() - t0

passed_n11 = result.returncode == 0
record(f"reproduce_n11.py passed ({elapsed:.1f}s)", passed_n11)
if not passed_n11:
    print(result.stdout[-2000:] if result.stdout else "")
    print(result.stderr[-1000:] if result.stderr else "")


# ── 3. Full test suite ────────────────────────────────────────────────────────
header("3. Full test suite (pytest)")

t0 = time.perf_counter()
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    cwd=str(PYTHON_DIR),
)
elapsed = time.perf_counter() - t0

# Extract summary line
summary_line = ""
for line in (result.stdout or "").splitlines():
    if "passed" in line or "failed" in line or "error" in line:
        summary_line = line.strip()
        break

passed_tests = result.returncode == 0
record(f"pytest passed  [{summary_line}]  ({elapsed:.1f}s)", passed_tests)
if not passed_tests:
    print((result.stdout or "")[-3000:])


# ── 4. Paper PDF build ───────────────────────────────────────────────────────
header("4. Paper PDF (pdflatex)")

import shutil
if shutil.which("pdflatex"):
    paper_dir = PYTHON_DIR / "paper"
    tex_file  = paper_dir / "preprint.tex"
    if tex_file.exists():
        t0 = time.perf_counter()
        for _ in range(2):   # twice for cross-refs
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "preprint.tex"],
                capture_output=True, cwd=str(paper_dir),
            )
        elapsed = time.perf_counter() - t0
        pdf = paper_dir / "preprint.pdf"
        record(f"preprint.pdf built  ({elapsed:.1f}s)", pdf.exists())
    else:
        warn("preprint.tex not found — skipping PDF build")
else:
    warn("pdflatex not found — skipping PDF build (install TeX Live or run make docker-run)")


# ── 5. Import smoke-test ─────────────────────────────────────────────────────
header("5. Import smoke-test")

smoke_imports = [
    ("monogate.BEST",                   "from monogate import BEST"),
    ("monogate.CBEST",                  "from monogate import CBEST"),
    ("monogate.complex_best_optimize",  "from monogate import complex_best_optimize"),
    ("monogate.im / re",                "from monogate import im, re"),
    ("monogate.ComplexOptimizeResult",  "from monogate import ComplexOptimizeResult"),
    ("monogate.complex_mcts_search",    "from monogate import complex_mcts_search"),
    ("monogate.complex_beam_search",    "from monogate import complex_beam_search"),
    ("monogate.best_optimize",          "from monogate import best_optimize"),
    ("monogate.context_aware_best_optimize", "from monogate import context_aware_best_optimize"),
    ("monogate.THEORY (THEORY.md)",     ""),   # file check, not import
]

for label, stmt in smoke_imports:
    if not stmt:
        # File check
        passed = (ROOT / "THEORY.md").exists()
        record(label, passed)
        continue
    try:
        exec(stmt)
        record(label, True)
    except ImportError as e:
        record(f"{label}  [{e}]", False)

# Optional torch-dependent imports
torch_imports = [
    ("monogate.EMLPINN",    "from monogate import EMLPINN"),
    ("monogate.fit_pinn",   "from monogate import fit_pinn"),
    ("monogate.EMLNetwork", "from monogate.network import EMLNetwork"),
]
for label, stmt in torch_imports:
    try:
        exec(stmt)
        record(f"{label} (torch)", True)
    except ImportError:
        warn(f"{label} — torch not installed, skipping")


# ── 6. Euler identity quick sanity ───────────────────────────────────────────
header("6. CBEST Euler identity sanity")

import math
try:
    from monogate import CBEST, im as _im
    z = CBEST.sin(math.pi / 6)
    got = _im(z)
    expected = math.sin(math.pi / 6)
    ok_euler = abs(got - expected) < 1e-10
    record(f"im(CBEST.sin(pi/6)) == 0.5  [got {got:.10f}]", ok_euler)
except Exception as e:
    record(f"CBEST Euler identity  [{e}]", False)


# ── Final summary ─────────────────────────────────────────────────────────────
n_pass = sum(1 for _, p in checks if p)
n_fail = sum(1 for _, p in checks if not p)

print()
print("=" * 60)
print(f"  monogate v0.11.0 release readiness — {n_pass} pass / {n_fail} fail")
print("=" * 60)
if n_fail == 0:
    print(f"\n  {GREEN}READY TO RELEASE.{RESET}")
    print()
    print("  Next steps:")
    print("    git tag v0.11.0 && git push origin v0.11.0")
    print("    python -m build && twine upload dist/*")
    print("    python scripts/update_arxiv_id.py 2604.XXXXX")
else:
    print(f"\n  {RED}NOT READY — fix the {n_fail} failing check(s) above.{RESET}")
print()

sys.exit(0 if n_fail == 0 else 1)
