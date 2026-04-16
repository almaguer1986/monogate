#!/usr/bin/env python3
"""
prepare_v0.10.py — v0.10.0 readiness script.

Runs all new v0.10.0 deliverables in sequence and prints a readiness summary:

  1. Import smoke test   — all new public APIs accessible
  2. Euler path check    — CBEST.sin/cos are exact (MSE ≈ 0)
  3. Complex BEST table  — CBEST.info() routing printout
  4. complex_best_optimize — sample expression analysis
  5. Complex MCTS        — sin(x) recovery (should find eml(ix, 1.0))
  6. PINN harmonic       — forward pass + fit (50 steps) completes without crash
  7. PINN Burgers        — forward pass + fit (50 steps) completes without crash
  8. Minimax MCTS        — objective='minimax' returns MCTSResult
  9. GPU search          — cpu-fallback path completes without crash
 10. Test suite          — pytest tests/test_complex_best.py tests/test_pinn.py
 11. Notebooks           — syntax check (compile without running heavy loops)

Usage::

    cd python
    python scripts/prepare_v0.10.py

Outputs:
    - Console readiness table
    - EXIT 0 if all checks pass, EXIT 1 otherwise

Requires: torch (pip install 'monogate[torch]')
"""

from __future__ import annotations

import math
import subprocess
import sys
import time
from typing import Callable

# ── Helpers ────────────────────────────────────────────────────────────────────

PASS  = "  PASS"
FAIL  = "  FAIL"
SKIP  = "  SKIP"

checks: list[tuple[str, str]] = []   # (name, status_line)


def run_check(name: str, fn: Callable[[], str | None]) -> None:
    """Run a check function, record pass/fail, print result."""
    t0 = time.perf_counter()
    try:
        note = fn() or ""
        elapsed = time.perf_counter() - t0
        status = f"{PASS}  ({elapsed:.2f}s)  {note}"
        ok = True
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        status = f"{FAIL}  ({elapsed:.2f}s)  {type(exc).__name__}: {exc}"
        ok = False
    checks.append((name, status))
    icon = "✓" if ok else "✗"
    print(f"  {icon}  {name:<45} {status}")


# ── Check implementations ──────────────────────────────────────────────────────

def check_imports() -> str:
    from monogate import (  # noqa: F401
        CBEST, ComplexHybridOperator, ComplexOptimizeResult,
        complex_best_optimize, im, re,
        SIN_NODE_COUNT, COS_NODE_COUNT, J0_NODE_COUNT, AI_NODE_COUNT, ERF_NODE_COUNT,
        complex_mcts_search, complex_beam_search,
        ComplexMCTSResult, ComplexBeamResult,
        EMLPINN, PINNResult, fit_pinn,
    )
    from monogate.search import gpu_mcts_search, GPUTreeEvaluator  # noqa: F401
    from monogate.search import mcts_search  # noqa: F401
    return "all new APIs importable"


def check_euler() -> str:
    from monogate import CBEST, im, re, sin_via_euler, cos_via_euler
    import math

    for x in [0.0, 0.5, 1.0, -1.0, math.pi / 4]:
        assert abs(im(CBEST.sin(x)) - math.sin(x)) < 1e-12, f"sin fail at {x}"
        assert abs(re(CBEST.cos(x)) - math.cos(x)) < 1e-12, f"cos fail at {x}"
    # Euler identity
    z = CBEST.exp(1j * math.pi)
    assert abs(z.real - (-1.0)) < 1e-10, "Euler identity failed"
    # sin_via_euler
    for x in [0.3, 1.7, -0.9]:
        assert abs(sin_via_euler(x) - math.sin(x)) < 1e-12

    return "sin/cos exact; Euler identity OK"


def check_cbest_table() -> str:
    from monogate import CBEST, SIN_NODE_COUNT, COS_NODE_COUNT
    assert SIN_NODE_COUNT == 1
    assert COS_NODE_COUNT == 1
    # Just exercise info() without printing to stdout in the script
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        CBEST.info()
    assert "sin" in buf.getvalue()
    return "routing table OK"


def check_complex_optimize() -> str:
    from monogate import complex_best_optimize
    result = complex_best_optimize("sin(x) + cos(x)")
    assert result.complex_savings_pct >= 90, f"expected ≥90% savings, got {result.complex_savings_pct}%"
    return f"sin+cos savings = {result.complex_savings_pct}%"


def check_complex_mcts() -> str:
    import math
    from monogate import complex_mcts_search
    result = complex_mcts_search(
        math.sin, projection="imag", depth=3, n_simulations=200, seed=0,
    )
    assert result.best_mse < 1e-10, f"MSE too high: {result.best_mse:.2e}"
    return f"sin recovered  mse={result.best_mse:.2e}  formula={result.complex_formula!r}"


def check_pinn_harmonic() -> str:
    try:
        import torch
    except ImportError:
        return "SKIP (torch not installed)"
    import math
    from monogate import EMLPINN, fit_pinn

    torch.manual_seed(0)
    model = EMLPINN(equation="harmonic", omega=2.0, backbone_depth=2)
    x = torch.linspace(0, math.pi, 20).unsqueeze(1)
    y = torch.sin(2.0 * x.squeeze(1))
    result = fit_pinn(model, x, y, x_phys=x, steps=50, log_every=0)
    assert math.isfinite(result.data_loss), "non-finite data_loss"
    assert math.isfinite(result.physics_loss), "non-finite physics_loss"
    assert len(result.formula) > 0
    return f"data={result.data_loss:.4f}  phys={result.physics_loss:.4f}"


def check_pinn_burgers() -> str:
    try:
        import torch
    except ImportError:
        return "SKIP (torch not installed)"
    import math
    import numpy as np
    from monogate import EMLPINN, fit_pinn

    torch.manual_seed(1)
    nu = 0.05
    x_np = np.linspace(-2, 2, 30)
    y_np = -nu * np.tanh(x_np / (2 * nu))
    x_data = torch.tensor(x_np, dtype=torch.float32).unsqueeze(1)
    y_data = torch.tensor(y_np, dtype=torch.float32)
    model = EMLPINN(equation="burgers", nu=nu, backbone_depth=2)
    result = fit_pinn(model, x_data, y_data, x_phys=x_data, steps=50, log_every=0)
    assert math.isfinite(result.data_loss)
    return f"data={result.data_loss:.4f}  phys={result.physics_loss:.4f}"


def check_minimax_mcts() -> str:
    import math
    from monogate.search import mcts_search
    r = mcts_search(math.exp, depth=3, n_simulations=200, objective="minimax")
    assert r.objective == "minimax"
    assert math.isfinite(r.best_mse)
    return f"objective={r.objective!r}  err={r.best_mse:.4e}"


def check_gpu_search() -> str:
    try:
        import torch  # noqa: F401
    except ImportError:
        return "SKIP (torch not installed)"
    import math
    from monogate.search import gpu_mcts_search
    # Always use CPU to avoid CUDA dependency in CI
    result = gpu_mcts_search(math.sin, device="cpu", batch_size=8, n_simulations=50, seed=0)
    assert math.isfinite(result.best_mse)
    return f"cpu fallback OK  mse={result.best_mse:.4e}"


def check_tests() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_complex_best.py", "tests/test_pinn.py",
         "-q", "--tb=short"],
        capture_output=True, text=True,
    )
    last_line = [l for l in proc.stdout.strip().splitlines() if l.strip()][-1] if proc.stdout.strip() else "no output"
    if proc.returncode != 0:
        raise RuntimeError(f"pytest failed:\n{proc.stdout[-800:]}\n{proc.stderr[-400:]}")
    return last_line


def check_notebook_syntax(path: str) -> None:
    """Compile-check a .py notebook without running it."""
    import ast
    with open(path, encoding="utf-8") as f:
        src = f.read()
    ast.parse(src)   # raises SyntaxError if broken


def check_notebooks() -> str:
    notebooks = [
        "notebooks/complex_special_functions.py",
        "notebooks/pinn_eml_demo.py",
        "notebooks/minimax_approximation.py",
    ]
    for nb in notebooks:
        check_notebook_syntax(nb)
    return f"{len(notebooks)} notebooks syntax-OK"


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    print()
    print("monogate v0.10.0 — Readiness Check")
    print("=" * 65)
    print()

    run_check("1. Import smoke test",        check_imports)
    run_check("2. Euler path (sin/cos exact)", check_euler)
    run_check("3. CBEST routing table",      check_cbest_table)
    run_check("4. complex_best_optimize",    check_complex_optimize)
    run_check("5. Complex MCTS sin(x)",      check_complex_mcts)
    run_check("6. PINN harmonic oscillator", check_pinn_harmonic)
    run_check("7. PINN steady Burgers",      check_pinn_burgers)
    run_check("8. Minimax MCTS objective",   check_minimax_mcts)
    run_check("9. GPU search (cpu fallback)", check_gpu_search)
    run_check("10. pytest new test files",   check_tests)
    run_check("11. Notebook syntax check",   check_notebooks)

    print()
    n_pass = sum(1 for _, s in checks if PASS in s)
    n_fail = sum(1 for _, s in checks if FAIL in s)
    n_skip = sum(1 for _, s in checks if "SKIP" in s)
    total  = len(checks)

    print("=" * 65)
    print(f"  Results: {n_pass}/{total} passed"
          + (f"  {n_fail} failed" if n_fail else "")
          + (f"  {n_skip} skipped" if n_skip else ""))

    if n_fail == 0:
        print()
        print("  ✓ v0.10.0 is ready.")
        print()
        print("  Next steps:")
        print("    git add -p && git commit -m 'feat: v0.10.0 — Complex BEST, PINN, minimax search'")
        print("    git push origin phase9-arxiv-live")
        print("    # Run full test suite: python -m pytest tests/ -q")
        return 0
    else:
        print()
        print(f"  ✗ {n_fail} check(s) failed — fix before release.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
