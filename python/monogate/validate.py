"""
monogate.validate — Challenge Board v2 submission validator.

Validates a JSON submission against the official probe points, computes
node counts (EML and BEST), and classifies the result as exact/tight/medium/
approximate/near_miss.

Usage (CLI):
    monogate-validate submission.json
    monogate-validate submission.json --problem lambert_w
    monogate-validate submission.json --fused --verbose
    monogate-validate --list-problems

Submission format (submission.json):
    {
      "problem_id": "lambert_w",
      "formula":    "eml(eml(1, eml(x, 1)), 1)",
      "submitter":  "your-github-handle",
      "notes":      "Optional description"
    }

Or with explicit tree JSON:
    {
      "problem_id": "lambert_w",
      "tree": {
        "op": "eml",
        "left": {"op": "leaf", "val": 1.0},
        "right": {"op": "eml",
                  "left": {"op": "leaf", "val": "x"},
                  "right": {"op": "leaf", "val": 1.0}}
      },
      "submitter": "your-handle"
    }
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "validate_submission", "ValidationResult",
    "load_problems", "list_problems",
]


# ── Tolerance tiers ────────────────────────────────────────────────────────────

TIERS = [
    ("exact",       1e-12),
    ("tight",       1e-8),
    ("medium",      1e-5),
    ("approximate", 1e-3),
    ("near_miss",   5e-2),
]

TIER_POINTS = {
    "exact":       10,
    "tight":       7,
    "medium":      4,
    "approximate": 2,
    "near_miss":   1,
    "none":        0,
}


# ── Formula parser & evaluator ─────────────────────────────────────────────────

def _parse_and_eval(s: str, x: float) -> float | None:
    """Recursively evaluate an eml(…) formula string at x."""
    s = s.strip()
    if s == "x":
        return x
    if s in ("1", "1.0"):
        return 1.0
    if s == "e":
        return math.e
    try:
        return float(s)
    except ValueError:
        pass

    if s.startswith("eml("):
        depth    = 0
        comma_at = -1
        for i, c in enumerate(s[4:], 4):
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    break
                depth -= 1
            elif c == "," and depth == 0:
                comma_at = i
                break

        if comma_at == -1:
            return None

        left_s  = s[4:comma_at].strip()
        right_s = s[comma_at + 1:s.rfind(")")].strip()

        lv = _parse_and_eval(left_s,  x)
        rv = _parse_and_eval(right_s, x)

        if lv is None or rv is None or rv <= 0:
            return None
        try:
            result = math.exp(lv) - math.log(rv)
            return result if math.isfinite(result) else None
        except (OverflowError, ValueError):
            return None

    return None


def _eval_tree_dict(node: dict, x: float) -> float | None:
    """Evaluate a tree dict node at x."""
    op = node.get("op")
    if op == "leaf":
        val = node["val"]
        if val == "x":
            return x
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
    if op == "eml":
        lv = _eval_tree_dict(node["left"],  x)
        rv = _eval_tree_dict(node["right"], x)
        if lv is None or rv is None or rv <= 0:
            return None
        try:
            r = math.exp(lv) - math.log(rv)
            return r if math.isfinite(r) else None
        except (OverflowError, ValueError):
            return None
    return None


# ── Node counting ──────────────────────────────────────────────────────────────

def _count_eml_nodes(formula: str) -> int:
    """Count the number of eml(...) calls in a formula string."""
    return formula.count("eml(")


def _count_best_nodes(formula: str) -> int:
    """
    BEST node count: count unique EML gates using optimal operator routing.

    This is an approximation for string formulas.  For exact counting,
    parse the tree and apply the BEST routing logic from monogate.core.
    """
    # Use the optimize module for a proper count if available
    try:
        from .optimize import best_optimize, optimize
        # If formula contains a target function representation, optimize it
        # Otherwise fall back to EML count (BEST always ≤ EML)
        return _count_eml_nodes(formula)  # Placeholder; real BEST count via optimize
    except ImportError:
        return _count_eml_nodes(formula)


# ── Validation ─────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Result of validating a submission against a challenge problem."""
    problem_id:   str
    formula:      str
    submitter:    str
    tier:         str
    points:       int
    max_error:    float
    mse:          float
    eml_nodes:    int
    best_nodes:   int
    savings_pct:  float
    eval_details: list[dict] = field(default_factory=list)
    errors:       list[str]  = field(default_factory=list)
    warnings:     list[str]  = field(default_factory=list)
    best_current: dict | None = None  # Current best known for this problem

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def beats_current_best(self) -> bool:
        if not self.best_current:
            return True  # No existing submission — first entry
        return self.mse < self.best_current.get("best_mse", float("inf"))

    def print_report(self) -> None:
        """Print a human-readable validation report."""
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        print()
        print("=" * 62)
        print(f"  monogate Challenge Validator — {self.problem_id}")
        print("=" * 62)
        print(f"  Formula:   {self.formula}")
        print(f"  Submitter: {self.submitter}")
        print()
        if self.errors:
            print("  ERRORS:")
            for e in self.errors:
                print(f"    - {e}")
        if self.warnings:
            print("  Warnings:")
            for w in self.warnings:
                print(f"    - {w}")
        print(f"  Max error: {self.max_error:.4e}")
        print(f"  MSE:       {self.mse:.4e}")
        print(f"  Tier:      {self.tier.upper()}  ({self.points} points)")
        print()
        print(f"  EML nodes:  {self.eml_nodes}")
        print(f"  BEST nodes: {self.best_nodes}")
        print(f"  Savings:    {self.savings_pct:.1f}%")
        print()

        if self.eval_details:
            print(f"  {'x':>8}  {'predicted':>12}  {'target':>12}  {'error':>12}")
            print("  " + "-" * 50)
            for d in self.eval_details[:10]:
                print(f"  {d['x']:>8.4f}  {d['predicted']:>12.6f}  "
                      f"{d['target']:>12.6f}  {d['error']:>12.2e}")

        if self.beats_current_best:
            print()
            print("  *** NEW BEST! This beats the current leaderboard entry. ***")
        print("=" * 62)
        print()

    def to_dict(self) -> dict:
        return {
            "problem_id":   self.problem_id,
            "formula":      self.formula,
            "submitter":    self.submitter,
            "tier":         self.tier,
            "points":       self.points,
            "max_error":    self.max_error,
            "mse":          self.mse,
            "eml_nodes":    self.eml_nodes,
            "best_nodes":   self.best_nodes,
            "savings_pct":  self.savings_pct,
            "is_valid":     self.is_valid,
            "beats_current": self.beats_current_best,
        }


def validate_submission(
    submission: dict,
    problems_path: str | Path | None = None,
    fused: bool = False,
    verbose: bool = False,
) -> ValidationResult:
    """
    Validate a submission dict against the challenge problem set.

    Args:
        submission:    Dict with keys: problem_id, formula (or tree), submitter.
        problems_path: Path to problems.json.  Defaults to challenge/problems.json
                       relative to the monogate package root.
        fused:         Use FusedEMLActivation for faster evaluation (torch required).
        verbose:       Print detailed evaluation table.

    Returns:
        ValidationResult with tier, points, node counts, and per-probe details.
    """
    # ── Load problems ─────────────────────────────────────────────────────
    problems = load_problems(problems_path)
    pid = submission.get("problem_id", "")
    problem = next((p for p in problems["problems"] if p["id"] == pid), None)
    if problem is None:
        return ValidationResult(
            problem_id=pid, formula="", submitter=submission.get("submitter", ""),
            tier="none", points=0, max_error=float("inf"), mse=float("inf"),
            eml_nodes=0, best_nodes=0, savings_pct=0.0,
            errors=[f"Unknown problem_id: {pid!r}. Use --list-problems to see available problems."],
        )

    # ── Extract formula ────────────────────────────────────────────────────
    formula   = submission.get("formula", "")
    tree_dict = submission.get("tree")
    submitter = submission.get("submitter", "anonymous")

    if not formula and tree_dict is None:
        return ValidationResult(
            problem_id=pid, formula="", submitter=submitter,
            tier="none", points=0, max_error=float("inf"), mse=float("inf"),
            eml_nodes=0, best_nodes=0, savings_pct=0.0,
            errors=["Submission must include 'formula' (string) or 'tree' (dict)."],
        )

    # ── Evaluate ───────────────────────────────────────────────────────────
    probe_x = problem["probe_x"]
    probe_y = problem["target_y"]

    eval_fn = (lambda x: _eval_tree_dict(tree_dict, x)) if tree_dict else \
              (lambda x: _parse_and_eval(formula, x))

    errors_list  = []
    warnings_list: list[str] = []
    eval_details: list[dict] = []
    squared_errors: list[float] = []

    for xi, yi in zip(probe_x, probe_y):
        pred = eval_fn(xi)
        if pred is None:
            errors_list.append(f"Formula returned None at x={xi} (domain error or invalid formula)")
            pred = float("inf")
        err = abs(pred - yi)
        squared_errors.append(err ** 2)
        eval_details.append({"x": xi, "predicted": pred, "target": yi, "error": err})

    if not squared_errors:
        max_error = float("inf")
        mse       = float("inf")
    else:
        max_error = max(abs(d["error"]) for d in eval_details
                        if math.isfinite(d["error"]))  if not errors_list else float("inf")
        mse       = (sum(squared_errors) / len(squared_errors)
                     if not errors_list else float("inf"))

    # ── Tier classification ───────────────────────────────────────────────
    tier   = "none"
    points = 0
    if max_error < float("inf"):
        for tier_name, tol in TIERS:
            if max_error < tol:
                tier   = tier_name
                points = TIER_POINTS[tier_name]
                break

    # ── Node counts ────────────────────────────────────────────────────────
    formula_for_count = formula or "(tree)"
    eml_nodes  = _count_eml_nodes(formula_for_count)
    best_nodes = eml_nodes  # TODO: wire to BEST optimizer

    try:
        from .optimize import best_optimize
        # Quick BEST count — needs a callable target; skip for string-only formulas
        pass
    except Exception:
        pass

    savings_pct = (1.0 - best_nodes / eml_nodes) * 100 if eml_nodes > 0 else 0.0

    # ── Leaderboard comparison ────────────────────────────────────────────
    leaderboard = load_leaderboard(problems_path)
    best_current = leaderboard.get("problem_stats", {}).get(pid)

    return ValidationResult(
        problem_id=pid,
        formula=formula or "(tree)",
        submitter=submitter,
        tier=tier,
        points=points,
        max_error=max_error,
        mse=mse,
        eml_nodes=eml_nodes,
        best_nodes=best_nodes,
        savings_pct=savings_pct,
        eval_details=eval_details,
        errors=errors_list,
        warnings=warnings_list,
        best_current=best_current,
    )


# ── Data loaders ──────────────────────────────────────────────────────────────

def _default_problems_dir() -> Path:
    return Path(__file__).parent.parent / "challenge"


def load_problems(path: str | Path | None = None) -> dict:
    """Load problems.json from the challenge directory."""
    if path is None:
        path = _default_problems_dir() / "problems.json"
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_leaderboard(problems_path: str | Path | None = None) -> dict:
    """Load leaderboard.json."""
    if problems_path is None:
        lb_path = _default_problems_dir() / "leaderboard.json"
    else:
        lb_path = Path(problems_path).parent / "leaderboard.json"
    if not lb_path.exists():
        return {"entries": [], "problem_stats": {}}
    return json.loads(lb_path.read_text(encoding="utf-8"))


def list_problems(problems_path: str | Path | None = None) -> None:
    """Print a human-readable list of all challenge problems."""
    data = load_problems(problems_path)
    lb   = load_leaderboard(problems_path)
    stats = lb.get("problem_stats", {})

    print()
    print("=" * 70)
    print("  monogate Challenge Board v2")
    print("=" * 70)
    print(f"  {'ID':<22}  {'Name':<22}  {'Difficulty':<12}  {'Best MSE':>10}  {'Pts':>4}")
    print("  " + "-" * 66)

    for p in data["problems"]:
        pid   = p["id"]
        s     = stats.get(pid, {})
        bmse  = s.get("best_mse")
        bmse_s = f"{bmse:.2e}" if bmse is not None else "open"
        pts   = p.get("points", "?")
        diff  = p.get("difficulty", "?")
        print(f"  {pid:<22}  {p['name']:<22}  {diff:<12}  {bmse_s:>10}  {pts:>4}")

    print("=" * 70)
    print()
    print("  Submit: create submission.json and run:")
    print("    monogate-validate submission.json")
    print()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="monogate Challenge Board v2 — submission validator"
    )
    parser.add_argument("submission", nargs="?", default=None,
                        help="Path to submission JSON file")
    parser.add_argument("--problem", default=None,
                        help="Override problem_id from CLI")
    parser.add_argument("--formula", default=None,
                        help="Formula string (instead of a JSON file)")
    parser.add_argument("--fused", action="store_true",
                        help="Use FusedEMLActivation for evaluation (requires torch)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full evaluation table")
    parser.add_argument("--list-problems", action="store_true",
                        help="List all challenge problems and exit")
    parser.add_argument("--problems-path", default=None,
                        help="Path to problems.json (default: challenge/problems.json)")
    parser.add_argument("--json-out", default=None,
                        help="Write validation result JSON to this path")

    args = parser.parse_args(argv)

    if args.list_problems:
        list_problems(args.problems_path)
        return

    submission: dict[str, Any] = {}

    if args.submission:
        path = Path(args.submission)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        submission = json.loads(path.read_text(encoding="utf-8"))

    if args.formula:
        submission["formula"] = args.formula
    if args.problem:
        submission["problem_id"] = args.problem

    if not submission:
        parser.print_help()
        sys.exit(0)

    result = validate_submission(
        submission,
        problems_path=args.problems_path,
        fused=args.fused,
        verbose=args.verbose,
    )
    result.print_report()

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(result.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"  Validation result saved → {args.json_out}")

    # Exit code: 0 = valid, 1 = invalid, 2 = error
    if result.errors:
        sys.exit(2)
    if result.tier == "none":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
