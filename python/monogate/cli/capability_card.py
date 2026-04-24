"""CapCard CLI — canonical card at capability_card_public.json.

Usage:
    python -m monogate capability-card --generate   # refresh derived fields
    python -m monogate capability-card --validate   # schema + version drift check
    python -m monogate capability-card --publish    # print real hosting targets
    python -m monogate capability-card --verify     # validate + benchmark assertions

The CLI operates on the single hand-curated card at the repo root:
    capability_card_public.json

--generate never clobbers curated content (capabilities, benchmarks, proofs,
integration). It only refreshes derived fields (version, test_count,
last_verified, metadata.updated, install command). Curated content is edited
by hand; this tool keeps the derived metadata in sync with the live package.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import monogate


REPO_SLUG = "almaguer1986/monogate"
LEAN_REPO_SLUG = "almaguer1986/monogate-lean"
SCHEMA_URL = "https://monogate.org/schemas/capcard/v3.json"
CAPCARD_SCHEMA_VERSION = "3"  # major version the CLI targets

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_CARD_PATH = _REPO_ROOT / "capability_card_public.json"
_SCHEMA_PATH = Path(__file__).parent.parent / "capability_card_schema.json"
_PYTHON_DIR = Path(__file__).parent.parent.parent

# Mirror paths — the card is also served publicly from the Astro blog and a
# well-known URL so agents can fetch it without guessing the GitHub raw URL.
_PUBLIC_MIRRORS = (
    _REPO_ROOT / "blog" / "public" / "capability_card.json",
    _REPO_ROOT / "blog" / "public" / ".well-known" / "capcard.json",
)

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[.+-].*)?$")
_CAPCARD_V3_RE = re.compile(r"^3\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _load_card() -> dict[str, Any]:
    if not _CARD_PATH.exists():
        raise FileNotFoundError(f"capability card not found: {_CARD_PATH}")
    with open(_CARD_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_card(card: dict[str, Any]) -> None:
    with open(_CARD_PATH, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _load_schema() -> dict[str, Any]:
    with open(_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _run_test_count() -> int:
    """Discover the test count via `pytest --co`. Returns -1 on any failure."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--co", "--tb=no"],
            capture_output=True, text=True, cwd=_PYTHON_DIR,
        )
        for line in result.stdout.splitlines():
            if "tests collected" in line or "test collected" in line:
                return int(line.split()[0])
    except Exception:
        pass
    return -1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# --generate
# ---------------------------------------------------------------------------

def generate_card() -> dict[str, Any]:
    """Refresh derived fields on the canonical card without touching curated sections."""
    card = _load_card()
    pkg_version = monogate.__version__
    now = _now_iso()

    changes: list[str] = []

    if card.get("version") != pkg_version:
        changes.append(f"version: {card.get('version')!r} -> {pkg_version!r}")
        card["version"] = pkg_version

    test_count = _run_test_count()
    verification = card.setdefault("verification", {})
    if test_count > 0 and verification.get("test_count") != test_count:
        changes.append(f"verification.test_count: {verification.get('test_count')} -> {test_count}")
        verification["test_count"] = test_count
    if verification.get("last_verified") != now:
        verification["last_verified"] = now
        changes.append("verification.last_verified: refreshed")

    metadata = card.setdefault("metadata", {})
    metadata["updated"] = now
    metadata.setdefault("created", now)
    if metadata.get("schema_url") != SCHEMA_URL:
        metadata["schema_url"] = SCHEMA_URL
        changes.append(f"metadata.schema_url -> {SCHEMA_URL}")

    integration = card.setdefault("integration", {})
    install = integration.setdefault("install", {})
    pip_spec = f"pip install monogate=={pkg_version}"
    if install.get("pip") != pip_spec:
        changes.append(f"integration.install.pip -> {pip_spec}")
        install["pip"] = pip_spec

    if not _validate_against_schema(card, strict=True):
        raise RuntimeError("refusing to write: card fails schema after generate")

    _write_card(card)

    # Mirror to public-facing locations so monogate.org/capability_card.json
    # and monogate.org/.well-known/capcard.json stay in sync with the canonical
    # card at the repo root.
    import json as _json
    mirrored: list[Path] = []
    for mirror in _PUBLIC_MIRRORS:
        try:
            mirror.parent.mkdir(parents=True, exist_ok=True)
            with open(mirror, "w", encoding="utf-8") as f:
                _json.dump(card, f, indent=2, ensure_ascii=False)
                f.write("\n")
            mirrored.append(mirror)
        except OSError as e:
            print(f"WARN  mirror write failed: {mirror} ({e})")

    print(f"CapCard written: {_CARD_PATH}")
    print(f"  version:      {pkg_version}")
    print(f"  test_count:   {verification.get('test_count', '?')}")
    print(f"  updated:      {now}")
    for m in mirrored:
        rel = m.relative_to(_REPO_ROOT) if m.is_relative_to(_REPO_ROOT) else m
        print(f"  mirrored:     {rel}")
    if changes:
        print("  changes:")
        for c in changes:
            print(f"    - {c}")
    else:
        print("  (no derived-field changes)")
    return card


# ---------------------------------------------------------------------------
# --validate
# ---------------------------------------------------------------------------

def _validate_against_schema(card: dict[str, Any], strict: bool) -> bool:
    try:
        import jsonschema
    except ImportError:
        if strict:
            print("WARN  jsonschema not installed; falling back to structural check")
        return _basic_validate(card)

    schema = _load_schema()
    try:
        jsonschema.validate(instance=card, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "(root)"
        print(f"FAIL  schema: at {path}: {e.message}")
        return False


def _basic_validate(card: dict[str, Any]) -> bool:
    required = [
        "capcard_version", "id", "name", "version", "description",
        "capabilities", "benchmarks", "proofs", "verification", "metadata",
    ]
    missing = [k for k in required if k not in card]
    if missing:
        print(f"FAIL  structure: missing required keys: {missing}")
        return False
    if not isinstance(card.get("capabilities"), list) or not card["capabilities"]:
        print("FAIL  structure: capabilities must be a non-empty array")
        return False
    return True


def _check_version_consistency(card: dict[str, Any]) -> bool:
    pkg = monogate.__version__
    card_ver = card.get("version")
    if not _SEMVER_RE.match(str(pkg)):
        print(f"FAIL  version: monogate.__version__={pkg!r} is not semver")
        return False
    if card_ver != pkg:
        print(f"FAIL  version drift: card={card_ver!r} vs package={pkg!r}  (run --generate)")
        return False
    return True


def validate_card() -> bool:
    """Validate schema + version consistency."""
    try:
        card = _load_card()
    except FileNotFoundError as e:
        print(f"FAIL  {e}")
        return False

    schema_ok = _validate_against_schema(card, strict=False)
    version_ok = _check_version_consistency(card)

    if schema_ok and version_ok:
        print(f"PASS  schema + version ({_CARD_PATH.name} v{card.get('version')})")
        _summary(card)
        return True
    return False


def _summary(card: dict[str, Any]) -> None:
    caps = card.get("capabilities", [])
    benches = card.get("benchmarks", [])
    proofs = card.get("proofs", [])
    ver = card.get("verification", {})
    n_lean_clean = ver.get("lean_clean_files")
    n_lean_partial = ver.get("lean_partial_files")
    n_lean_sorries = ver.get("lean_sorries_total")
    print(f"  capcard:      v{card.get('capcard_version', '?')}")
    print(f"  capabilities: {len(caps)}")
    print(f"  benchmarks:   {len(benches)}")
    print(f"  proofs:       {len(proofs)} ({sum(1 for p in proofs if p.get('sorries', 1) == 0)} with 0 sorries)")
    if n_lean_clean is not None:
        print(f"  lean files:   {n_lean_clean} clean + {n_lean_partial or 0} partial ({n_lean_sorries or 0} sorries total)")
    print(f"  test_count:   {ver.get('test_count', '?')}")
    print(f"  last_verified: {ver.get('last_verified', '?')}")


# ---------------------------------------------------------------------------
# --publish
# ---------------------------------------------------------------------------

def publish_card() -> None:
    """Print the real hosting targets for the card."""
    try:
        card = _load_card()
        version = card.get("version", monogate.__version__)
    except FileNotFoundError:
        version = monogate.__version__
        card = {}

    raw_url = f"https://raw.githubusercontent.com/{REPO_SLUG}/master/{_CARD_PATH.name}"
    blob_url = f"https://github.com/{REPO_SLUG}/blob/master/{_CARD_PATH.name}"
    pypi_url = f"https://pypi.org/project/monogate/{version}/"
    homepage = card.get("homepage", "https://monogate.org")

    print("CapCard hosting targets")
    print("=" * 60)
    print(f"  local path:   {_CARD_PATH}")
    print(f"  GitHub blob:  {blob_url}")
    print(f"  GitHub raw:   {raw_url}")
    print( "  public URL:   https://monogate.org/capability_card.json")
    print( "  well-known:   https://monogate.org/.well-known/capcard.json")
    print(f"  PyPI:         {pypi_url}")
    print(f"  homepage:     {homepage}")
    print(f"  schema:       {SCHEMA_URL}")
    print()
    print("Refresh derived fields and commit:")
    print("  python -m monogate capability-card --generate")
    print("  python -m monogate capability-card --verify")
    print(f"  git add {_CARD_PATH.name} python/monogate/capability_card_schema.json")
    print("  git commit -m 'chore(capcard): refresh derived fields'")
    print("  git push")


# ---------------------------------------------------------------------------
# --verify benchmark assertions
# ---------------------------------------------------------------------------

def _find_capability(card: dict[str, Any], cap_id: str) -> dict[str, Any] | None:
    for c in card.get("capabilities", []):
        if c.get("id") == cap_id:
            return c
    return None


def _assert_exp_identity() -> tuple[str, str]:
    import math
    from monogate.core import op
    for x in (0.5, 1.0, 2.0):
        err = abs(op(x, 1.0) - math.exp(x))
        if err >= 1e-12:
            return "FAIL", f"exp identity: err={err:.3e} at x={x}"
    return "PASS", "exp identity: eml(x, 1) = exp(x)"


def _assert_abs_identity() -> tuple[str, str]:
    from monogate.core import op
    for x in (0.5, 1.0, 3.14):
        got = op(1.0, op(op(1.0, op(x, 1.0)), 1.0))
        err = abs(got - x)
        if err >= 1e-11:
            return "FAIL", f"abs identity: err={err:.3e} at x={x}"
    return "PASS", "EML identity theorem: eml(1, eml(eml(1, eml(x, 1)), 1)) = x"


def _assert_version_consistency(card: dict[str, Any]) -> tuple[str, str]:
    pkg = monogate.__version__
    card_ver = card.get("version")
    if not _SEMVER_RE.match(str(pkg)):
        return "FAIL", f"monogate.__version__={pkg!r} not semver"
    if card_ver != pkg:
        return "FAIL", f"version drift: card={card_ver!r} vs package={pkg!r}"
    return "PASS", f"version consistency: {pkg}"


def _assert_test_count() -> tuple[str, str]:
    n = _run_test_count()
    if n < 0:
        return "WARN", "test_count: pytest --co unavailable"
    if n < 1500:
        return "FAIL", f"test_count: {n} < 1500"
    return "PASS", f"test_count: {n} >= 1500"


def _assert_superbest_card(card: dict[str, Any]) -> tuple[str, str]:
    cap = _find_capability(card, "routing.superbest_v5")
    if cap is None:
        return "FAIL", "superbest card: routing.superbest_v5 missing"
    c = cap.get("constraints", {})
    expect = {"total_nodes": 14, "naive_total": 73, "savings_percent": 80.8}
    for k, v in expect.items():
        got = c.get(k)
        if got != v:
            return "FAIL", f"superbest card: {k}={got!r} expected {v!r}"
    return "PASS", "superbest card: 14n / 80.8% / 73 naive"


def _assert_superbest_package(card: dict[str, Any]) -> tuple[str, str]:
    try:
        from monogate.superbest import superbest_summary
    except Exception as e:
        return "FAIL", f"superbest package: import failed ({e})"
    try:
        headline = superbest_summary(positive_domain=True)
    except Exception as e:
        return "FAIL", f"superbest package: call failed ({e})"
    match = re.search(r"(\d+)n\s*/\s*([\d.]+)%", str(headline))
    if match is None:
        return "FAIL", "superbest package: could not parse headline"
    pkg_nodes = int(match.group(1))
    pkg_savings = float(match.group(2))
    cap = _find_capability(card, "routing.superbest_v5") or {}
    c = cap.get("constraints", {})
    card_nodes = c.get("total_nodes")
    card_savings = c.get("savings_percent")
    if pkg_nodes != card_nodes or abs(pkg_savings - float(card_savings or 0)) > 0.1:
        return "FAIL", (
            f"superbest drift: package={pkg_nodes}n/{pkg_savings}% vs "
            f"card={card_nodes}n/{card_savings}%"
        )
    return "PASS", f"superbest package: {pkg_nodes}n / {pkg_savings}% agrees with card"


def _assert_taxonomy(card: dict[str, Any]) -> tuple[str, str]:
    cap = _find_capability(card, "taxonomy.sixteen_operators")
    if cap is None:
        return "FAIL", "taxonomy: capability missing"
    c = cap.get("constraints", {})
    total = c.get("operators_count")
    complete = c.get("complete")
    approx = c.get("approximate")
    incomplete = c.get("incomplete")
    if None in (total, complete, approx, incomplete):
        return "FAIL", f"taxonomy: missing constraints {c}"
    if complete + approx + incomplete != total:
        return "FAIL", f"taxonomy: {complete}+{approx}+{incomplete} != {total}"
    if (total, complete, approx, incomplete) != (16, 8, 1, 7):
        return "FAIL", f"taxonomy: got (16/8/1/7) expected but saw ({total}/{complete}/{approx}/{incomplete})"
    return "PASS", "taxonomy: 16 = 8 complete + 1 approximate + 7 incomplete"


def _assert_catalog_315(card: dict[str, Any]) -> tuple[str, str]:
    cap = _find_capability(card, "catalog.equations_315")
    if cap is None:
        return "FAIL", "catalog: catalog.equations_315 missing"
    size = cap.get("constraints", {}).get("catalog_size")
    if size != 315:
        return "FAIL", f"catalog: size={size!r} expected 315"
    return "PASS", "catalog: 315 equations"


def _assert_lean_proofs(card: dict[str, Any]) -> tuple[str, str]:
    proofs = card.get("proofs", [])
    if len(proofs) < 10:
        return "FAIL", f"lean proofs: {len(proofs)} < 10"
    clean = sum(1 for p in proofs if p.get("sorries", -1) == 0)
    partial = [p for p in proofs if p.get("sorries", 0) > 0]
    total_sorries = sum(p.get("sorries", 0) for p in proofs)
    if clean < 9:
        return "FAIL", f"lean proofs: {clean} with 0 sorries (expected >= 9)"
    if total_sorries != 2:
        return "FAIL", f"lean proofs: total sorries = {total_sorries} (expected 2)"
    if len(partial) != 1 or partial[0].get("sorries") != 2:
        partial_desc = [(p.get("id"), p.get("sorries")) for p in partial]
        return "FAIL", f"lean proofs: expected exactly one partial with 2 sorries; got {partial_desc}"
    return "PASS", f"lean proofs: {len(proofs)} total, {clean} clean, 1 partial (2 sorries)"


def _assert_core_capabilities(card: dict[str, Any]) -> tuple[str, str]:
    required = [
        "universality.eml",
        "taxonomy.sixteen_operators",
        "routing.superbest_v5",
        "characterization.elc_real",
        "barrier.infinite_zeros",
        "bridge.euler_gateway",
        "cost.decomposition",
    ]
    missing = [cid for cid in required if _find_capability(card, cid) is None]
    if missing:
        return "FAIL", f"core capabilities missing: {missing}"
    return "PASS", f"core capabilities present ({len(required)})"


# ── v3 assertions ──────────────────────────────────────────────────────────

def _assert_capcard_v3(card: dict[str, Any]) -> tuple[str, str]:
    ver = card.get("capcard_version", "")
    if not _CAPCARD_V3_RE.match(str(ver)):
        return "FAIL", f"capcard_version={ver!r} — CLI targets v3.x.x"
    return "PASS", f"capcard_version: {ver}"


def _assert_verification_lean_counts(card: dict[str, Any]) -> tuple[str, str]:
    """v3 requires verification.lean_clean_files + lean_partial_files + lean_sorries_total."""
    v = card.get("verification", {})
    clean = v.get("lean_clean_files")
    partial = v.get("lean_partial_files")
    sorries = v.get("lean_sorries_total")
    if None in (clean, partial, sorries):
        return "FAIL", "verification: lean_clean_files / lean_partial_files / lean_sorries_total required in v3"
    if clean < 11:
        return "FAIL", f"verification: lean_clean_files={clean} < 11"
    if partial > 1:
        return "FAIL", f"verification: lean_partial_files={partial} > 1 — unexpected partial file"
    if sorries > 2:
        return "FAIL", f"verification: lean_sorries_total={sorries} > 2 — regression vs last audit"
    return "PASS", f"verification: lean {clean} clean + {partial} partial ({sorries} sorries)"


def _assert_neural_capabilities(card: dict[str, Any]) -> tuple[str, str]:
    """v3: softplus / sigmoid / adam / rmsnorm tool_function capabilities carry neural_metrics."""
    required = {
        "activation.softplus": {"forward_nodes": 1},
        "activation.sigmoid":  {"forward_nodes": 5},
        "optimizer.adam":      {"optimizer_nodes_per_param_per_step": 31},
        "norm.rmsnorm":        {"forward_nodes": 4097},
    }
    missing: list[str] = []
    mismatch: list[str] = []
    for cap_id, expected in required.items():
        cap = _find_capability(card, cap_id)
        if cap is None:
            missing.append(cap_id)
            continue
        nm = cap.get("neural_metrics") or {}
        for k, want in expected.items():
            got = nm.get(k)
            if got != want:
                mismatch.append(f"{cap_id}.neural_metrics.{k} = {got!r} (expected {want!r})")
    if missing:
        return "FAIL", f"v3 neural capabilities missing: {missing}"
    if mismatch:
        return "FAIL", "; ".join(mismatch)
    return "PASS", "v3 neural caps: softplus=1n, sigmoid=5n, Adam=31n, RMSNorm=4097n"


def _assert_adam_31n(card: dict[str, Any]) -> tuple[str, str]:
    """Explicit check that the post-NN-13 re-audit value propagated."""
    adam = _find_capability(card, "optimizer.adam")
    if adam is None:
        return "FAIL", "optimizer.adam capability missing"
    nm = adam.get("neural_metrics") or {}
    n = nm.get("optimizer_nodes_per_param_per_step")
    em = adam.get("eml_metrics") or {}
    sb = em.get("superbest_nodes")
    if n != 31:
        return "FAIL", f"Adam per-param-per-step = {n!r}, expected 31 (post-NN-13 re-audit)"
    if sb is not None and sb != 31:
        return "FAIL", f"Adam eml_metrics.superbest_nodes = {sb!r}, expected 31"
    return "PASS", "Adam re-audit: 31n per param per step (post-NN-13)"


BenchmarkFn = Callable[[], tuple[str, str]]


def _run_benchmarks(card: dict[str, Any]) -> tuple[bool, list[tuple[str, str]]]:
    checks: list[BenchmarkFn] = [
        lambda: _assert_capcard_v3(card),
        _assert_exp_identity,
        _assert_abs_identity,
        lambda: _assert_version_consistency(card),
        _assert_test_count,
        lambda: _assert_superbest_card(card),
        lambda: _assert_superbest_package(card),
        lambda: _assert_taxonomy(card),
        lambda: _assert_catalog_315(card),
        lambda: _assert_lean_proofs(card),
        lambda: _assert_verification_lean_counts(card),
        lambda: _assert_core_capabilities(card),
        lambda: _assert_neural_capabilities(card),
        lambda: _assert_adam_31n(card),
    ]
    results: list[tuple[str, str]] = []
    for fn in checks:
        try:
            results.append(fn())
        except Exception as e:
            results.append(("FAIL", f"{fn.__name__ if hasattr(fn, '__name__') else 'check'}: unexpected exception {e!r}"))
    passed = all(status != "FAIL" for status, _ in results)
    return passed, results


def verify_card() -> bool:
    """Validate schema + version + run benchmark assertions."""
    print("CapCard Verification")
    print("=" * 60)

    try:
        card = _load_card()
    except FileNotFoundError as e:
        print(f"FAIL  {e}")
        return False

    schema_ok = _validate_against_schema(card, strict=False)
    version_ok = _check_version_consistency(card)
    if schema_ok:
        print(f"PASS  schema ({_CARD_PATH.name})")
    if version_ok:
        print(f"PASS  version ({card.get('version')})")

    print()
    print("Benchmark assertions:")
    all_pass, results = _run_benchmarks(card)
    for status, msg in results:
        print(f"  {status:4}  {msg}")

    print()
    if schema_ok and version_ok and all_pass:
        print("RESULT: ALL CHECKS PASSED")
        _summary(card)
        return True
    print("RESULT: SOME CHECKS FAILED")
    return False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    import argparse
    parser = argparse.ArgumentParser(description="monogate CapCard CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true", help="Refresh derived fields on capability_card_public.json")
    group.add_argument("--validate", action="store_true", help="Validate schema + version consistency")
    group.add_argument("--publish", action="store_true", help="Print real hosting targets for the card")
    group.add_argument("--verify",   action="store_true", help="Validate + run benchmark assertions")
    args = parser.parse_args(argv)

    if args.generate:
        generate_card()
    elif args.validate:
        if not validate_card():
            sys.exit(1)
    elif args.publish:
        publish_card()
    elif args.verify:
        if not verify_card():
            sys.exit(1)


if __name__ == "__main__":
    main()
