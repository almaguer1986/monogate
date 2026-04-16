#!/usr/bin/env python3
"""
scripts/update_arxiv_id.py — Replace ARXIV_ID_PLACEHOLDER with the real arXiv ID.

Usage:
    python scripts/update_arxiv_id.py 2604.XXXXX
    python scripts/update_arxiv_id.py 2604.XXXXX --dry-run
    python scripts/update_arxiv_id.py 2604.XXXXX --no-backup

After submission, get your arXiv ID from https://arxiv.org/user/  (e.g. 2604.12345)
and run this script from the python/ directory.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Force UTF-8 output on Windows (cp1252 cannot encode em-dashes in diffs)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Files that contain ARXIV_ID_PLACEHOLDER ──────────────────────────────────

PLACEHOLDER = "ARXIV_ID_PLACEHOLDER"

# Paths relative to the script's parent directory (python/)
TARGETS: list[dict] = [
    {
        "path": "README.md",
        "description": "Main README — badge and BibTeX entry",
    },
    {
        "path": "assets/n11_share_card.md",
        "description": "N=11 share card — paper section",
    },
    {
        "path": "../explorer/src/components/ResearchTab.jsx",
        "description": "Explorer ResearchTab — paper banner href",
    },
    {
        "path": "../explorer/src/components/LeaderboardTab.jsx",
        "description": "Explorer LeaderboardTab — arXiv reference banner href",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _diff_lines(before: str, after: str, path: str) -> list[str]:
    """Return a compact list of changed lines (no difflib dependency needed)."""
    lines_before = before.splitlines()
    lines_after  = after.splitlines()
    diffs: list[str] = []
    for i, (a, b) in enumerate(zip(lines_before, lines_after), start=1):
        if a != b:
            diffs.append(f"  line {i:4d}  - {a.strip()}")
            diffs.append(f"  line {i:4d}  + {b.strip()}")
    return diffs


def _validate_arxiv_id(arxiv_id: str) -> None:
    """Fail early if the ID looks wrong (e.g. forgot to strip the arXiv: prefix)."""
    clean = arxiv_id.strip()
    if clean.lower().startswith("arxiv:"):
        print(f"  Tip: strip the 'arXiv:' prefix — pass just the numeric ID.")
        sys.exit(1)
    # Basic format check: YYMM.NNNNN or YYMM.NNNNN[vN]
    import re
    if not re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", clean):
        print(
            f"  Warning: '{clean}' doesn't match the expected arXiv ID format "
            f"(YYMM.NNNNN or YYMM.NNNNNvN).\n"
            f"  Continuing anyway — double-check before committing."
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace ARXIV_ID_PLACEHOLDER with the real arXiv ID.",
        epilog="Example: python scripts/update_arxiv_id.py 2604.12345",
    )
    parser.add_argument("arxiv_id", help="arXiv ID, e.g. 2604.12345")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing any files.",
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip creating .bak files before editing.",
    )
    args = parser.parse_args()

    arxiv_id  = args.arxiv_id.strip()
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

    _validate_arxiv_id(arxiv_id)

    print()
    print("=" * 60)
    print(f"  monogate — arXiv ID update")
    print(f"  Placeholder : {PLACEHOLDER}")
    print(f"  New ID      : {arxiv_id}")
    print(f"  arXiv URL   : {arxiv_url}")
    if args.dry_run:
        print("  Mode        : DRY RUN (no files will be changed)")
    print("=" * 60)
    print()

    root = Path(__file__).parent.parent   # python/

    changed = 0
    skipped = 0

    for entry in TARGETS:
        path = (root / entry["path"]).resolve()
        desc = entry["description"]

        print(f"  [{path.name}]  {desc}")

        if not path.exists():
            print(f"    SKIP — file not found: {path}")
            skipped += 1
            continue

        original = path.read_text(encoding="utf-8")

        JSX_SENTINEL = 'const ARXIV_ID  = "";   // ARXIV_ID_PLACEHOLDER — leave empty until submitted'
        is_jsx = path.suffix in (".jsx", ".tsx", ".js", ".ts")
        search_term = JSX_SENTINEL if is_jsx else PLACEHOLDER

        if search_term not in original:
            count = original.count(arxiv_id)
            if count:
                print(f"    OK   — already updated ({count} occurrence(s) of the real ID found)")
            else:
                print(f"    SKIP — placeholder not found and real ID not present")
            skipped += 1
            continue

        n_replacements = original.count(search_term)

        # Build the updated content.
        # JSX files use empty-string sentinel: const ARXIV_ID = "";
        # Only replace that one line — don't touch comment text which still has the
        # word "ARXIV_ID_PLACEHOLDER" (it's just documentation).
        if path.suffix in (".jsx", ".tsx", ".js", ".ts"):
            updated = original.replace(
                'const ARXIV_ID  = "";   // ARXIV_ID_PLACEHOLDER — leave empty until submitted',
                f'const ARXIV_ID  = "{arxiv_id}";',
            )
        else:
            # Markdown / Python files: straight placeholder replacement.
            updated = original.replace(PLACEHOLDER, arxiv_id)

        # README: also promote badge URL and status text
        if path.name == "README.md":
            updated = updated.replace(
                "[![arXiv](https://img.shields.io/badge/arXiv-link%20pending-b31b1b)](paper/preprint.tex)",
                f"[![arXiv](https://img.shields.io/badge/arXiv-{arxiv_id}-b31b1b)](https://arxiv.org/abs/{arxiv_id})",
            )
            updated = updated.replace(
                "> arXiv ID: **[link pending — will update after submission]**",
                f"> arXiv ID: **[{arxiv_id}](https://arxiv.org/abs/{arxiv_id})**",
            )
            updated = updated.replace(
                "**Paper submission-ready**",
                "**Now on arXiv**",
            )

        # share_card: update the self-referential hint line
        if path.name == "n11_share_card.md":
            updated = updated.replace(
                f"*Update {arxiv_id}: `python scripts/update_arxiv_id.py <id>`*",
                f"*Paper ID: {arxiv_id}  (run `python scripts/update_arxiv_id.py <new-id>` to re-run)*",
            )

        # Also update the badge URL in README.md from local preprint.tex to live arXiv
        if path.name == "README.md":
            updated = updated.replace(
                "[![arXiv](https://img.shields.io/badge/arXiv-link%20pending-b31b1b)](paper/preprint.tex)",
                f"[![arXiv](https://img.shields.io/badge/arXiv-{arxiv_id}-b31b1b)](https://arxiv.org/abs/{arxiv_id})",
            )
            updated = updated.replace(
                "> arXiv ID: **[link pending — will update after submission]**",
                f"> arXiv ID: **[{arxiv_id}](https://arxiv.org/abs/{arxiv_id})**",
            )
            updated = updated.replace(
                "**Paper submission-ready**",
                "**Now on arXiv**",
            )

        diffs = _diff_lines(original, updated, str(path))
        print(f"    {n_replacements} replacement(s)  ({len(diffs)//2} changed line(s))")
        for d in diffs:
            print(d)

        if not args.dry_run:
            if not args.no_backup:
                backup = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, backup)
                print(f"    Backup  -> {backup.name}")
            path.write_text(updated, encoding="utf-8")
            print(f"    Written -> {path.name}")
            changed += 1
        else:
            changed += 1   # count "would change"

        print()

    print("=" * 60)
    if args.dry_run:
        print(f"  DRY RUN complete. {changed} file(s) would be updated, {skipped} skipped.")
    else:
        print(f"  Done. {changed} file(s) updated, {skipped} skipped.")
        if changed:
            print()
            print("  Next steps:")
            print(f"    1. Review the diffs above.")
            print(f"    2. git add -p   (stage selectively)")
            print(f"    3. git commit -m 'chore: update arXiv ID to {arxiv_id}'")
            print(f"    4. Rebuild the explorer:  cd ../explorer && npm run build")
            print(f"    5. Publish to PyPI:       cd python && python -m build && twine upload dist/*")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
