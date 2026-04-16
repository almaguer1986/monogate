#!/usr/bin/env python3
"""
release_v1.1.0.py — Release readiness check for monogate v1.1.0.

Checks in order:
  1. Version verification (__init__.py + pyproject.toml both == 1.1.0)
  2. Full test suite (pytest)
  3. Import smoke-test: core + prover + neural scorer
  4. Prover sanity: prove two identities end-to-end
  5. Neural scorer sanity: score, update, retrain cycle
  6. Identity catalog: ≥150 entries, no duplicates
  7. Package build (python -m build)

Usage::

    cd python
    python scripts/release_v1.1.0.py

Exit code 0 = all checks passed, ready to tag and push.
Exit code 1 = one or more checks failed.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent   # repo root
PYTHON_DIR = ROOT / "python"

EXPECTED_VERSION = "1.1.0"

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str)     -> None: print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg: str)   -> None: print(f"  {RED}[FAIL]{RESET}  {msg}")
def warn(msg: str)   -> None: print(f"  {YELLOW}[SKIP]{RESET}  {msg}")
def header(msg: str) -> None:
    print(f"\n{BOLD}{msg}{RESET}")
    print("-" * len(msg))

checks: list[tuple[str, bool]] = []

def record(label: str, passed: bool) -> bool:
    checks.append((label, passed))
    (ok if passed else fail)(label)
    return passed


# ── 1. Version check ──────────────────────────────────────────────────────────
header("1. Version verification")

init_path      = PYTHON_DIR / "monogate" / "__init__.py"
pyproject_path = PYTHON_DIR / "pyproject.toml"

init_version = None
for line in init_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("__version__"):
        init_version = line.split('"')[1]
        break

pyproject_version = None
for line in pyproject_path.read_text(encoding="utf-8").splitlines():
    if line.strip().startswith("version"):
        pyproject_version = line.split('"')[1]
        break

record(f"__init__.py  version == {EXPECTED_VERSION}  [got {init_version}]",
       init_version == EXPECTED_VERSION)
record(f"pyproject.toml version == {EXPECTED_VERSION}  [got {pyproject_version}]",
       pyproject_version == EXPECTED_VERSION)


# ── 2. Full test suite ────────────────────────────────────────────────────────
header("2. Full test suite (pytest)")

t0 = time.perf_counter()
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    cwd=str(PYTHON_DIR),
)
elapsed = time.perf_counter() - t0

summary_line = ""
for line in (result.stdout or "").splitlines():
    if "passed" in line or "failed" in line or "error" in line:
        summary_line = line.strip()

passed_tests = result.returncode == 0
record(f"pytest  [{summary_line}]  ({elapsed:.1f}s)", passed_tests)
if not passed_tests:
    print((result.stdout or "")[-3000:])


# ── 3. Import smoke-test ──────────────────────────────────────────────────────
header("3. Import smoke-test")

smoke = [
    # Core
    ("monogate.BEST",                    "from monogate import BEST"),
    ("monogate.CBEST",                   "from monogate import CBEST"),
    ("monogate.best_optimize",           "from monogate import best_optimize"),
    ("monogate.EMLRegressor",            "from monogate import EMLRegressor"),
    ("monogate.Interval / eml_interval", "from monogate import Interval, eml_interval"),
    # Prover
    ("monogate.EMLProver",               "from monogate import EMLProver"),
    ("monogate.EMLProverV2",             "from monogate import EMLProverV2"),
    ("monogate.ProofResult",             "from monogate import ProofResult"),
    ("monogate.ALL_IDENTITIES",          "from monogate import ALL_IDENTITIES"),
    ("monogate.get_by_category",         "from monogate import get_by_category"),
    # Neural scorer
    ("monogate.FeatureBasedEMLScorer",   "from monogate import FeatureBasedEMLScorer"),
    ("monogate.ExperienceBuffer",        "from monogate import ExperienceBuffer"),
    ("monogate.extract_tree_features",   "from monogate import extract_tree_features"),
    ("monogate.N_FEATURES",              "from monogate import N_FEATURES"),
    # Research modules
    ("monogate.MinimaxResult",           "from monogate import MinimaxResult"),
    ("monogate.PHYSICS_CATALOG",         "from monogate import PHYSICS_CATALOG"),
    ("monogate.PAdicNumber",             "from monogate import PAdicNumber"),
    ("monogate.ReactionLaw",             "from monogate import ReactionLaw"),
    ("monogate.EMLCausalModel",          "from monogate import EMLCausalModel"),
]

for label, stmt in smoke:
    try:
        exec(stmt)
        record(label, True)
    except ImportError as e:
        record(f"{label}  [{e}]", False)

# Optional torch-dependent
for label, stmt in [
    ("monogate.EMLPINN (torch)",  "from monogate import EMLPINN"),
    ("monogate.EMLNetwork (torch)", "from monogate.network import EMLNetwork"),
]:
    try:
        exec(stmt)
        record(f"{label}", True)
    except ImportError:
        warn(f"{label} — torch not installed")


# ── 4. Prover end-to-end sanity ───────────────────────────────────────────────
header("4. Prover end-to-end sanity")

try:
    from monogate.prover import EMLProverV2  # type: ignore

    p = EMLProverV2()

    # Simple exact proof
    r1 = p.prove("exp(x) == exp(x)")
    record("prove('exp(x) == exp(x)') → proved", r1.proved())

    # Pythagorean identity
    r2 = p.prove("sin(x)**2 + cos(x)**2 == 1")
    record("prove('sin²+cos²==1') → proved", r2.proved())

    # Confidence is 1.0 for exact proofs
    record(f"confidence == 1.0  [got {r2.confidence}]", r2.confidence == 1.0)

    # Conjecture generation
    conjectures = p.generate_conjectures(n=5)
    record(f"generate_conjectures returned {len(conjectures)} items", len(conjectures) > 0)

except Exception as e:
    record(f"Prover end-to-end  [{e}]", False)


# ── 5. Neural scorer sanity ───────────────────────────────────────────────────
header("5. Neural scorer sanity")

try:
    import numpy as np
    from monogate import FeatureBasedEMLScorer, extract_tree_features, N_FEATURES
    from monogate.search.mcts import _eml, _leaf  # type: ignore

    tree = _eml(_leaf("x"), _leaf(1.0))
    feat = extract_tree_features(tree)

    record(f"N_FEATURES == 12  [got {N_FEATURES}]", N_FEATURES == 12)
    record(f"extract_tree_features shape == ({N_FEATURES},)",
           feat.shape == (N_FEATURES,))
    record("all features finite", all(np.isfinite(feat)))

    s = FeatureBasedEMLScorer(min_samples=5, retrain_every=5)
    record("untrained score == 0.5", abs(s.score(tree) - 0.5) < 1e-9)
    record("is_trained() == False initially", not s.is_trained())

    for _ in range(6):
        s.update(tree, 0.8)
    record("is_trained() after 6 updates", s.is_trained())
    score = s.score(tree)
    record(f"trained score in [0,1]  [got {score:.4f}]", 0.0 <= score <= 1.0)

except Exception as e:
    record(f"Neural scorer  [{e}]", False)


# ── 6. Identity catalog ───────────────────────────────────────────────────────
header("6. Identity catalog")

try:
    from monogate.identities import ALL_IDENTITIES  # type: ignore

    n = len(ALL_IDENTITIES)
    record(f"ALL_IDENTITIES has ≥150 entries  [got {n}]", n >= 150)

    exprs = [i.expression for i in ALL_IDENTITIES]
    dupes = len(exprs) - len(set(exprs))
    record(f"No duplicate expressions  [{dupes} dupes]", dupes == 0)

except Exception as e:
    record(f"Identity catalog  [{e}]", False)


# ── 7. Package build ──────────────────────────────────────────────────────────
header("7. Package build (python -m build)")

import shutil
if shutil.which("build") or True:   # always attempt via -m build
    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", "dist/"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(PYTHON_DIR),
    )
    elapsed = time.perf_counter() - t0
    passed_build = result.returncode == 0
    record(f"python -m build --wheel  ({elapsed:.1f}s)", passed_build)
    if not passed_build:
        print((result.stderr or "")[-2000:])
else:
    warn("build not available — run: pip install build")


# ── Final summary ─────────────────────────────────────────────────────────────
n_pass = sum(1 for _, p in checks if p)
n_fail = sum(1 for _, p in checks if not p)

print()
print("=" * 64)
print(f"  {BOLD}monogate v1.1.0 release readiness{RESET}"
      f" — {n_pass} pass / {n_fail} fail")
print("=" * 64)

if n_fail == 0:
    print(f"\n  {GREEN}{BOLD}READY TO RELEASE.{RESET}")
    print()
    print("  Next steps:")
    print("    git tag v1.1.0 && git push origin v1.1.0")
    print("    twine upload dist/monogate-1.1.0-*.whl")
    print()
    print("  Announce:")
    print("    PyPI  : https://pypi.org/project/monogate/1.1.0/")
    print("    GitHub: https://github.com/almaguer1986/monogate/releases")
else:
    print(f"\n  {RED}{BOLD}NOT READY — fix the {n_fail} failing check(s) above.{RESET}")

print()
sys.exit(0 if n_fail == 0 else 1)
