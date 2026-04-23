"""Tests for the CapCard CLI (python/monogate/cli/capability_card.py).

The canonical card lives at the repo root (capability_card_public.json);
these tests avoid mutating it by running against a deep-copied fixture.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

import monogate
from monogate.cli import capability_card as cc


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def canonical_card() -> dict:
    assert cc._CARD_PATH.exists(), f"canonical card missing at {cc._CARD_PATH}"
    with open(cc._CARD_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mutable_card(canonical_card: dict) -> dict:
    return deepcopy(canonical_card)


@pytest.fixture
def isolated_card(tmp_path: Path, canonical_card: dict, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect _CARD_PATH at a tmp copy so --generate never touches the real file."""
    tmp_card = tmp_path / "capability_card_public.json"
    with open(tmp_card, "w", encoding="utf-8") as f:
        json.dump(canonical_card, f, indent=2)
    monkeypatch.setattr(cc, "_CARD_PATH", tmp_card)
    return tmp_card


# ---------------------------------------------------------------------------
# schema + basic shape
# ---------------------------------------------------------------------------

def test_schema_file_exists_and_parses():
    schema = cc._load_schema()
    assert schema.get("$id", "").startswith("https://")
    assert "capabilities" in schema["properties"]
    assert "proofs" in schema["properties"]


def test_canonical_card_passes_schema(canonical_card):
    assert cc._validate_against_schema(canonical_card, strict=False) is True


def test_canonical_card_passes_basic_validate(canonical_card):
    assert cc._basic_validate(canonical_card) is True


# ---------------------------------------------------------------------------
# version + consistency
# ---------------------------------------------------------------------------

def test_card_version_matches_package(canonical_card):
    assert canonical_card["version"] == monogate.__version__


def test_check_version_consistency_accepts_canonical(canonical_card):
    assert cc._check_version_consistency(canonical_card) is True


def test_check_version_consistency_rejects_drift(mutable_card):
    mutable_card["version"] = "0.0.0"
    assert cc._check_version_consistency(mutable_card) is False


# ---------------------------------------------------------------------------
# benchmark assertions — probe the canonical card
# ---------------------------------------------------------------------------

def test_exp_identity_assertion_passes():
    status, _ = cc._assert_exp_identity()
    assert status == "PASS"


def test_abs_identity_assertion_passes():
    status, _ = cc._assert_abs_identity()
    assert status == "PASS"


def test_superbest_card_claims_15n_79_5(canonical_card):
    status, msg = cc._assert_superbest_card(canonical_card)
    assert status == "PASS", msg


def test_taxonomy_8_1_7(canonical_card):
    status, msg = cc._assert_taxonomy(canonical_card)
    assert status == "PASS", msg


def test_taxonomy_rejects_bad_sum(mutable_card):
    cap = cc._find_capability(mutable_card, "taxonomy.sixteen_operators")
    cap["constraints"]["incomplete"] = 6  # 8+1+6 != 16
    status, _ = cc._assert_taxonomy(mutable_card)
    assert status == "FAIL"


def test_catalog_315(canonical_card):
    status, msg = cc._assert_catalog_315(canonical_card)
    assert status == "PASS", msg


def test_lean_proof_accounting(canonical_card):
    status, msg = cc._assert_lean_proofs(canonical_card)
    assert status == "PASS", msg


def test_lean_proof_rejects_too_few(mutable_card):
    mutable_card["proofs"] = mutable_card["proofs"][:5]
    status, _ = cc._assert_lean_proofs(mutable_card)
    assert status == "FAIL"


def test_core_capabilities_present(canonical_card):
    status, msg = cc._assert_core_capabilities(canonical_card)
    assert status == "PASS", msg


def test_core_capabilities_detects_missing(mutable_card):
    mutable_card["capabilities"] = [
        c for c in mutable_card["capabilities"]
        if c.get("id") != "characterization.elc_real"
    ]
    status, _ = cc._assert_core_capabilities(mutable_card)
    assert status == "FAIL"


def test_superbest_package_agrees_with_card(canonical_card):
    # Post v5.2 update, the package must agree with the card — no drift allowed.
    status, msg = cc._assert_superbest_package(canonical_card)
    assert status == "PASS", msg


def test_superbest_package_detects_drift(canonical_card, monkeypatch: pytest.MonkeyPatch):
    def fake_summary(positive_domain: bool = False) -> str:
        return "SuperBEST vFake - 99n / 12.3% savings vs naive 113n baseline"
    monkeypatch.setattr("monogate.superbest.superbest_summary", fake_summary)
    status, _ = cc._assert_superbest_package(canonical_card)
    assert status == "FAIL"


# ---------------------------------------------------------------------------
# --generate idempotency and preservation
# ---------------------------------------------------------------------------

def test_generate_preserves_curated_sections(isolated_card: Path):
    before = json.loads(isolated_card.read_text(encoding="utf-8"))
    cc.generate_card()
    after = json.loads(isolated_card.read_text(encoding="utf-8"))

    for key in ("capabilities", "benchmarks", "proofs", "authors", "related_sites"):
        assert after.get(key) == before.get(key), f"--generate mutated curated {key}"


def test_generate_sets_version_and_pip_spec(isolated_card: Path):
    cc.generate_card()
    card = json.loads(isolated_card.read_text(encoding="utf-8"))
    assert card["version"] == monogate.__version__
    assert card["integration"]["install"]["pip"] == f"pip install monogate=={monogate.__version__}"
    assert card["metadata"]["schema_url"] == cc.SCHEMA_URL


def test_generate_is_idempotent_on_version_and_schema(isolated_card: Path):
    cc.generate_card()
    snap1 = json.loads(isolated_card.read_text(encoding="utf-8"))
    cc.generate_card()
    snap2 = json.loads(isolated_card.read_text(encoding="utf-8"))
    # Only last_verified/metadata.updated (time-varying) may differ.
    for key in ("version", "capabilities", "benchmarks", "proofs",
                "integration", "capcard_version", "id", "name"):
        assert snap1.get(key) == snap2.get(key), f"--generate mutated {key} on re-run"


# ---------------------------------------------------------------------------
# CLI exit codes via main()
# ---------------------------------------------------------------------------

def test_validate_exit_zero_on_canonical(isolated_card: Path, capsys: pytest.CaptureFixture):
    # No SystemExit -> exit code 0.
    cc.main(["--validate"])
    out = capsys.readouterr().out
    assert "PASS" in out


def test_validate_exits_nonzero_on_version_drift(isolated_card: Path):
    data = json.loads(isolated_card.read_text(encoding="utf-8"))
    data["version"] = "0.0.0"
    isolated_card.write_text(json.dumps(data, indent=2), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        cc.main(["--validate"])
    assert exc.value.code == 1


def test_publish_prints_real_urls(capsys: pytest.CaptureFixture):
    cc.main(["--publish"])
    out = capsys.readouterr().out
    assert f"github.com/{cc.REPO_SLUG}" in out
    assert "raw.githubusercontent.com" in out
    assert "pypi.org/project/monogate" in out
    assert "capcard.ai" not in out  # the stale URL is gone


def test_publish_does_not_reference_removed_capcard_site(capsys: pytest.CaptureFixture):
    cc.main(["--publish"])
    out = capsys.readouterr().out
    assert "capcard_site" not in out
    assert "GitHub Pages" not in out


def test_main_requires_a_mode():
    with pytest.raises(SystemExit):
        cc.main([])


# ---------------------------------------------------------------------------
# v3 schema + neural-capability + Adam re-audit
# ---------------------------------------------------------------------------

def test_capcard_version_is_v3(canonical_card):
    status, _ = cc._assert_capcard_v3(canonical_card)
    assert status == "PASS"


def test_capcard_version_rejects_v2(mutable_card):
    mutable_card["capcard_version"] = "2.0.0"
    status, _ = cc._assert_capcard_v3(mutable_card)
    assert status == "FAIL"


def test_verification_lean_counts_present(canonical_card):
    v = canonical_card["verification"]
    assert v.get("lean_clean_files") == 11
    assert v.get("lean_partial_files") == 1
    assert v.get("lean_sorries_total") == 2


def test_verification_lean_counts_assertion_passes(canonical_card):
    status, _ = cc._assert_verification_lean_counts(canonical_card)
    assert status == "PASS"


def test_verification_lean_counts_rejects_regression(mutable_card):
    mutable_card["verification"]["lean_sorries_total"] = 5
    status, _ = cc._assert_verification_lean_counts(mutable_card)
    assert status == "FAIL"


def test_neural_capabilities_softplus_adam_rmsnorm(canonical_card):
    status, msg = cc._assert_neural_capabilities(canonical_card)
    assert status == "PASS", msg


def test_neural_capabilities_detects_missing_softplus(mutable_card):
    mutable_card["capabilities"] = [
        c for c in mutable_card["capabilities"]
        if c.get("id") != "activation.softplus"
    ]
    status, _ = cc._assert_neural_capabilities(mutable_card)
    assert status == "FAIL"


def test_adam_31n_assertion(canonical_card):
    """Post-NN-13 re-audit: Adam must be 31n, not the original 37n."""
    status, msg = cc._assert_adam_31n(canonical_card)
    assert status == "PASS", msg


def test_adam_31n_rejects_reverted_37n(mutable_card):
    adam = cc._find_capability(mutable_card, "optimizer.adam")
    adam["neural_metrics"]["optimizer_nodes_per_param_per_step"] = 37
    status, _ = cc._assert_adam_31n(mutable_card)
    assert status == "FAIL"


def test_schema_requires_capcard_v3_pattern():
    schema = cc._load_schema()
    pat = schema["properties"]["capcard_version"].get("pattern")
    assert pat == r"^3\.\d+\.\d+$"


def test_v3_schema_id_is_canonical():
    schema = cc._load_schema()
    assert schema["$id"] == "https://monogate.org/schemas/capcard/v3.json"
