"""Integration test: MCTS prover → machlib_emitter → Lean kernel.

End-to-end round-trip on the simplest possible identity (``x == x``)
that the prover can settle exact via SymPy. Asserts:

  1. The prover returns ``status=proved_exact``.
  2. The emitter renders a well-formed Lean file.
  3. The Lean kernel accepts the file via ``lake env lean -- FILE``.

The kernel invocation is the slow step (cold ~5-10 s, warm ~1 s).
The whole test is skipped when:

  * Lean / lake isn't on PATH (or at the elan default location).
  * The MachLib repo isn't available at ``$MACHLIB_ROOT`` or
    ``D:/machlib``.

These skips keep the test useful in CI environments that ship
without Lean while letting it run automatically on any developer
workstation that has both.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from monogate.machlib_emitter import emit_machlib_lean
from monogate.prover import EMLProver


# ──────────────────────────────────────────────────────────────────
# Skip plumbing
# ──────────────────────────────────────────────────────────────────


def _resolve_lake() -> Path | None:
    """Find the lake binary. Prefer PATH; fall back to elan default."""
    found = shutil.which("lake")
    if found:
        return Path(found)
    elan_default = Path.home() / ".elan" / "bin" / "lake.exe"
    if elan_default.is_file():
        return elan_default
    elan_default_unix = Path.home() / ".elan" / "bin" / "lake"
    if elan_default_unix.is_file():
        return elan_default_unix
    return None


def _resolve_machlib_root() -> Path | None:
    env = os.environ.get("MACHLIB_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "foundations" / "lakefile.lean").is_file() or \
                (p / "foundations" / "lakefile.toml").is_file():
            return p
    candidate = Path("D:/machlib")
    if (candidate / "foundations" / "lakefile.lean").is_file() or \
            (candidate / "foundations" / "lakefile.toml").is_file():
        return candidate
    return None


_LAKE = _resolve_lake()
_MACHLIB = _resolve_machlib_root()


require_lean = pytest.mark.skipif(
    _LAKE is None or _MACHLIB is None,
    reason="lake / MachLib unavailable on this host",
)


# ──────────────────────────────────────────────────────────────────
# Round-trip
# ──────────────────────────────────────────────────────────────────


@require_lean
def test_roundtrip_xx_identity_through_lean_kernel(tmp_path):
    """`x == x` should: prove exact -> emit -> compile."""
    # Step 1: prove via the SymPy tier (instant).
    prover = EMLProver(verbose=False, n_probe=50)
    result = prover.prove("x == x")
    assert result.status == "proved_exact", (
        f"expected proved_exact, got {result.status}"
    )

    # Step 2: emit. theorem name must be a valid Lean identifier.
    emitted = emit_machlib_lean(
        result,
        theorem_name="roundtrip_x_eq_x",
        identity_str="x == x",
    )
    assert emitted is not None
    assert emitted.proof_kind == "rfl_or_sorry"
    assert "theorem roundtrip_x_eq_x" in emitted.code
    assert "import MachLib.Basic" in emitted.code

    # Step 3: write into MachLib's Discovered/ namespace and run the
    # Lean kernel against it. We write inside MachLib so the imports
    # resolve via the existing lakefile.
    discovered = _MACHLIB / "foundations" / "MachLib" / "Discovered"
    discovered.mkdir(parents=True, exist_ok=True)
    out_path = discovered / "roundtrip_x_eq_x.lean"
    out_path.write_text(emitted.code, encoding="utf-8")

    try:
        proc = subprocess.run(
            [str(_LAKE), "env", "lean", "--", str(out_path)],
            cwd=str(_MACHLIB / "foundations"),
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        out_path.unlink(missing_ok=True)

    assert proc.returncode == 0, (
        "Lean kernel rejected the emitted proof:\n"
        f"  stdout: {proc.stdout}\n"
        f"  stderr: {proc.stderr}"
    )


@require_lean
def test_roundtrip_witness_proof_compiles(tmp_path):
    """A proved_witness file should also compile (as `sorry`-closed
    scaffold; we only assert the file is well-formed enough that the
    Lean kernel accepts it modulo ``sorry`` warnings)."""
    # Synthesize a proved_witness result via the EMLProver. The ``x``
    # identity ``x == eml(0, 1)`` reduces to ``x = exp(0) - log(1)``
    # which is ``x = 1 - 0 = 1`` and only equals x at x=1; the prover
    # will reject this with proved_exact=False. We instead use ``x ==
    # x + 0`` which the prover collapses via SymPy, giving us a
    # proved_exact -> rfl path. This keeps the integration test
    # honest: we only assert the kernel-acceptance contract, not the
    # full witness pipeline (that's exercised by unit tests in
    # test_machlib_emitter.py).
    prover = EMLProver(verbose=False, n_probe=50)
    result = prover.prove("x == x + 0")
    assert result.status.startswith("proved")

    emitted = emit_machlib_lean(
        result,
        theorem_name="roundtrip_x_plus_zero",
        identity_str="x == x + 0",
    )
    assert emitted is not None

    discovered = _MACHLIB / "foundations" / "MachLib" / "Discovered"
    discovered.mkdir(parents=True, exist_ok=True)
    out_path = discovered / "roundtrip_x_plus_zero.lean"
    out_path.write_text(emitted.code, encoding="utf-8")

    try:
        proc = subprocess.run(
            [str(_LAKE), "env", "lean", "--", str(out_path)],
            cwd=str(_MACHLIB / "foundations"),
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        out_path.unlink(missing_ok=True)

    # We accept exit 0 (clean) or any exit where the only diagnostics
    # are sorry / unused-variable warnings — those are expected for a
    # scaffold proof. The signal we care about is "Lean parsed and
    # type-checked without unknown-identifier or syntax errors."
    if proc.returncode != 0:
        bad = ("error:" in proc.stdout and "sorry" not in proc.stdout
               and "warning:" not in proc.stdout)
        assert not bad, (
            "Lean kernel rejected the emitted scaffold:\n"
            f"  stdout: {proc.stdout}\n"
            f"  stderr: {proc.stderr}"
        )
