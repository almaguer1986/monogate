#!/usr/bin/env python3
"""
Compile the private routing table into a distributable binary.

    python scripts/compile_routing.py

Reads:  private _routing_private.py (not in public repo)
Writes: monogate/_routing.pkl          (binary, shipped in PyPI wheel)

The private source file lives OUTSIDE the public repo (gitignored and moved
out of the package tree for safety). Lookup order:
  1. $MONOGATE_ROUTING_PRIVATE  — explicit filesystem path
  2. ../monogate-research/private_routing/_routing_private.py
  3. ../../monogate-research/private_routing/_routing_private.py

The binary is included in PyPI wheels via pyproject.toml package-data so that
the installed package loads the full optimized dispatch table at import time.
Run this script after any change to _routing_private.py, then rebuild the wheel.
"""

from __future__ import annotations

import importlib.util
import os
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # python/


def _locate_private_source() -> Path:
    """Return the path to the private _routing_private.py source file."""
    env = os.environ.get("MONOGATE_ROUTING_PRIVATE")
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_file():
            return p
        sys.exit(f"ERROR: MONOGATE_ROUTING_PRIVATE points to missing file: {p}")

    candidates = [
        ROOT.parent.parent / "monogate-research" / "private_routing"
            / "_routing_private.py",
        ROOT.parent / "monogate-research" / "private_routing"
            / "_routing_private.py",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    sys.exit(
        "ERROR: _routing_private.py not found.\n"
        "Looked in $MONOGATE_ROUTING_PRIVATE and the standard\n"
        "monogate-research/private_routing/ location.\n"
        "The private file must exist outside the public repo tree."
    )


def _load_routing_table(src: Path) -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("_routing_private", src)
    if spec is None or spec.loader is None:
        sys.exit(f"ERROR: failed to load {src}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    table = getattr(module, "ROUTING_TABLE", None)
    if not isinstance(table, dict) or not table:
        sys.exit(
            f"ERROR: ROUTING_TABLE in {src} is empty or malformed."
        )
    return {str(k): str(v) for k, v in table.items()}


def main() -> None:
    src = _locate_private_source()
    table = _load_routing_table(src)

    out_path = ROOT / "monogate" / "_routing.pkl"
    with out_path.open("wb") as fh:
        pickle.dump(table, fh, protocol=pickle.HIGHEST_PROTOCOL)

    size = out_path.stat().st_size
    print(f"Source:  {src}")
    print(f"Written: {out_path}  ({size} bytes, {len(table)} ops)")
    for op, name in sorted(table.items()):
        print(f"  {op:<8} -> {name}")


if __name__ == "__main__":
    main()
