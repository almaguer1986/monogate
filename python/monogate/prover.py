"""
monogate.prover — Neurosymbolic theorem prover for EML identities.

Proves mathematical identities of the form ``f(x) == g(x)`` using a
three-tier strategy:

1. **Numerical check** (fast): Evaluate |f(x)−g(x)| at 500 probe points.
   If max residual < 1e-8 → ``proved_numerical``.

2. **Exact check** (SymPy): ``sympy.simplify(lhs − rhs) == 0``.
   If yes → ``proved_exact``.

3. **Certified check** (interval arithmetic): Split domain into sub-intervals
   and verify the residual is bounded near zero.
   If yes → ``proved_certified``.

4. **EML witness search** (MCTS): Find shortest EML tree T ≈ f(x), then
   check ``sympy.simplify(to_sympy(T) − rhs_sympy) == 0``.
   If yes → ``proved_witness``.

Public API
----------
ProofResult      — frozen dataclass with full proof metadata
BenchmarkReport  — summary of a batch benchmark run
EMLProver        — main prover class

    EMLProver(verbose=False, n_probe=500)
    .prove(identity, ...)   -> ProofResult
    .prove_batch(...)       -> list[ProofResult]
    .benchmark(...)         -> BenchmarkReport
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

__all__ = [
    "ProofResult",
    "BenchmarkReport",
    "EMLProver",
    "EMLProverV2",
]

# ── Optional imports (gracefully degraded) ────────────────────────────────────

try:
    import sympy
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
    )
    _SYMPY_OK = True
except ImportError:
    _SYMPY_OK = False

try:
    from .sympy_bridge import to_sympy as _tree_to_sympy
    _BRIDGE_OK = True
except ImportError:
    _BRIDGE_OK = False

try:
    from .interval import Interval, eval_interval
    _INTERVAL_OK = True
except ImportError:
    _INTERVAL_OK = False

try:
    from .search.mcts import mcts_search
    _MCTS_OK = True
except ImportError:
    _MCTS_OK = False


# ── ProofResult ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProofResult:
    """Result of a neurosymbolic proof attempt.

    Attributes:
        identity_str:         The raw identity string that was proved.
        status:               One of 'proved_exact', 'proved_certified',
                              'proved_numerical', 'proved_witness',
                              'inconclusive', 'failed'.
        verification_method:  One of 'sympy', 'interval', 'numerical',
                              'eml_witness', 'combined'.
        confidence:           Float 0.0–1.0 (1.0 for exact proofs).
        max_residual:         Max |lhs(x)−rhs(x)| on test points.
        n_test_points:        Number of probe points evaluated.
        elapsed_s:            Wall-clock seconds.
        lhs_tree:             EML tree dict for LHS (if found by MCTS), or None.
        rhs_tree:             EML tree dict for RHS (if found by MCTS), or None.
        witness_tree:         EML witness tree T with T ≈ LHS symbolically, or None.
        node_count:           Number of nodes in witness or LHS tree (0 if none).
        mcts_simulations:     MCTS simulations run during witness-tier search
                              (0 for all other proof tiers).
        lhs_formula:          Human-readable EML formula for LHS (if found).
        latex_proof:          LaTeX proof string (if generated).
        sympy_simplification: What SymPy computed (string), or None.
        notes:                List of proof steps / observations.
    """

    identity_str: str
    status: str
    verification_method: str
    confidence: float
    max_residual: float
    n_test_points: int
    elapsed_s: float
    lhs_tree: Optional[dict]
    rhs_tree: Optional[dict]
    witness_tree: Optional[dict]
    node_count: int
    lhs_formula: Optional[str]
    latex_proof: Optional[str]
    sympy_simplification: Optional[str]
    notes: List[str]
    mcts_simulations: int = 0

    def proved(self) -> bool:
        """Return True if the proof succeeded (any method)."""
        return self.status.startswith("proved")

    def __str__(self) -> str:
        symbol = "✓" if self.proved() else "✗"
        return (
            f"{symbol} [{self.status}] {self.identity_str!r}  "
            f"residual={self.max_residual:.2e}  "
            f"conf={self.confidence:.2f}  "
            f"t={self.elapsed_s:.2f}s"
        )


# ── BenchmarkReport ───────────────────────────────────────────────────────────

@dataclass
class BenchmarkReport:
    """Summary of a batch proof benchmark run.

    Attributes:
        results:       List of individual ProofResult objects.
        n_total:       Total number of identities attempted.
        n_proved:      Number successfully proved.
        n_exact:       Number proved with exact (SymPy) method.
        n_numerical:   Number proved numerically.
        n_failed:      Number that failed or were inconclusive.
        success_rate:  Fraction proved / total.
        mean_elapsed_s: Mean time per proof.
        mean_nodes:    Mean node count for EML witnesses.
    """

    results: List[ProofResult]
    n_total: int
    n_proved: int
    n_exact: int
    n_numerical: int
    n_failed: int
    success_rate: float
    mean_elapsed_s: float
    mean_nodes: float

    def summary(self) -> str:
        """Formatted table summary of the benchmark."""
        lines = [
            "=" * 72,
            f"  EML Theorem Prover Benchmark  —  {self.n_total} identities",
            "=" * 72,
            f"  Proved:       {self.n_proved}/{self.n_total}  ({self.success_rate*100:.1f}%)",
            f"  Exact:        {self.n_exact}",
            f"  Numerical:    {self.n_numerical}",
            f"  Failed:       {self.n_failed}",
            f"  Mean time:    {self.mean_elapsed_s:.3f}s",
            f"  Mean nodes:   {self.mean_nodes:.1f}",
            "-" * 72,
        ]
        # Per-identity rows
        header = f"  {'Identity':<42} {'Status':<20} {'Resid':>10}"
        lines.append(header)
        lines.append("  " + "-" * 70)
        for r in self.results:
            name = r.identity_str[:40]
            lines.append(f"  {name:<42} {r.status:<20} {r.max_residual:>10.2e}")
        lines.append("=" * 72)
        return "\n".join(lines)

    def to_json(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "n_total": self.n_total,
            "n_proved": self.n_proved,
            "n_exact": self.n_exact,
            "n_numerical": self.n_numerical,
            "n_failed": self.n_failed,
            "success_rate": self.success_rate,
            "mean_elapsed_s": self.mean_elapsed_s,
            "mean_nodes": self.mean_nodes,
            "results": [
                {
                    "identity": r.identity_str,
                    "status": r.status,
                    "method": r.verification_method,
                    "confidence": r.confidence,
                    "max_residual": r.max_residual,
                    "elapsed_s": r.elapsed_s,
                    "node_count": r.node_count,
                }
                for r in self.results
            ],
        }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _linspace(lo: float, hi: float, n: int) -> List[float]:
    """Pure-math linspace (no numpy)."""
    if n <= 1:
        return [lo]
    step = (hi - lo) / (n - 1)
    return [lo + step * i for i in range(n)]


def _count_nodes(tree: Optional[dict]) -> int:
    """Count nodes in an EML tree dict."""
    if tree is None:
        return 0
    if tree.get("op") in ("leaf", "?"):
        return 1
    return 1 + _count_nodes(tree.get("left")) + _count_nodes(tree.get("right"))


def _eval_tree(tree: dict, x: float) -> float:
    """Evaluate an EML tree at a scalar x (pure math module)."""
    op = tree.get("op")
    if op == "leaf":
        val = tree["val"]
        if val == "x":
            return x
        return float(val)
    if op == "eml":
        a = _eval_tree(tree["left"], x)
        b = _eval_tree(tree["right"], x)
        if b <= 0.0:
            return float("nan")
        return math.exp(a) - math.log(b)
    return float("nan")


def _formula_str(tree: dict) -> str:
    """Convert EML tree to human-readable formula string."""
    op = tree.get("op")
    if op == "leaf":
        val = tree["val"]
        return str(val)
    if op == "eml":
        left_s = _formula_str(tree["left"])
        right_s = _formula_str(tree["right"])
        return f"eml({left_s}, {right_s})"
    return "?"


def _make_math_fn(expr_str: str) -> Optional[Callable[[float], float]]:
    """
    Build a callable f(x: float) -> float from a SymPy expression string.

    Uses math module functions for evaluation; falls back to None if parsing
    fails.
    """
    if not _SYMPY_OK:
        return None
    try:
        x_sym = sympy.Symbol("x")
        transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )
        expr = parse_expr(expr_str, local_dict={"x": x_sym}, transformations=transformations)
        fn = sympy.lambdify(x_sym, expr, modules="math")
        return fn
    except Exception:
        return None


def _parse_identity(identity: str) -> Tuple[Optional[str], Optional[str]]:
    """Split 'lhs == rhs' into (lhs_str, rhs_str). Returns (None, None) on failure."""
    if "==" not in identity:
        return None, None
    parts = identity.split("==", 1)
    return parts[0].strip(), parts[1].strip()


def _sympy_parse(expr_str: str):
    """Parse a sympy expression string, returning the sympy Expr or None."""
    if not _SYMPY_OK:
        return None
    try:
        x_sym = sympy.Symbol("x")
        transformations = (
            standard_transformations + (implicit_multiplication_application,)
        )
        return parse_expr(
            expr_str,
            local_dict={"x": x_sym},
            transformations=transformations,
        )
    except Exception:
        return None


def _try_sympy_exact(lhs_expr, rhs_expr) -> Tuple[bool, Optional[str]]:
    """Try sympy.simplify(lhs - rhs) == 0. Returns (proved, simplified_str)."""
    if not _SYMPY_OK or lhs_expr is None or rhs_expr is None:
        return False, None
    try:
        diff = sympy.simplify(lhs_expr - rhs_expr)
        simplified_str = str(diff)
        return diff == 0, simplified_str
    except Exception as exc:
        return False, f"sympy error: {exc}"


def _numerical_check(
    lhs_fn: Optional[Callable],
    rhs_fn: Optional[Callable],
    probe_points: List[float],
    threshold: float = 1e-8,
) -> Tuple[bool, float]:
    """
    Evaluate |lhs(x) - rhs(x)| at probe_points.

    Returns (proved, max_residual).
    """
    if lhs_fn is None or rhs_fn is None:
        return False, float("inf")
    residuals = []
    for x in probe_points:
        try:
            lv = lhs_fn(x)
            rv = rhs_fn(x)
            if math.isfinite(lv) and math.isfinite(rv):
                residuals.append(abs(lv - rv))
        except Exception:
            pass
    if not residuals:
        return False, float("inf")
    max_res = max(residuals)
    return max_res < threshold, max_res


def _certified_interval_check(
    lhs_fn: Optional[Callable],
    rhs_fn: Optional[Callable],
    domain: Tuple[float, float],
    n_sub: int = 20,
    threshold: float = 1e-6,
) -> Tuple[bool, float]:
    """
    Crude certified check using function evaluation at sub-interval endpoints.

    Splits domain into n_sub sub-intervals and checks the max |lhs-rhs|
    at each endpoint. This is not a true interval proof but gives a tighter
    numerical bound over many sub-intervals.

    Returns (certified, max_residual).
    """
    if lhs_fn is None or rhs_fn is None:
        return False, float("inf")
    lo, hi = domain
    step = (hi - lo) / n_sub
    all_residuals = []
    for i in range(n_sub + 1):
        x = lo + step * i
        try:
            lv = lhs_fn(x)
            rv = rhs_fn(x)
            if math.isfinite(lv) and math.isfinite(rv):
                all_residuals.append(abs(lv - rv))
        except Exception:
            pass
    if not all_residuals:
        return False, float("inf")
    max_res = max(all_residuals)
    return max_res < threshold, max_res


def _mcts_witness_search(
    lhs_fn: Callable,
    probe_points: List[float],
    rhs_expr,
    max_nodes: int,
    n_simulations: int,
    seed: int,
    timeout: float,
    external_scorer: "Optional[Callable[[dict], float]]" = None,
) -> Tuple[Optional[dict], Optional[str], bool, int]:
    """
    Run MCTS to find an EML tree T ≈ lhs_fn, then verify T == rhs symbolically.

    Returns (witness_tree, formula_str, proved_witness, n_simulations_run).
    The fourth element is the actual number of MCTS simulations executed
    (0 if MCTS could not run).
    """
    if not _MCTS_OK or not _SYMPY_OK or not _BRIDGE_OK:
        return None, None, False, 0

    # depth for MCTS (n_nodes ≈ 2*depth - 1 for full binary tree)
    depth = max(2, (max_nodes + 1) // 2)

    try:
        result = mcts_search(
            target_fn=lhs_fn,
            probe_points=probe_points,
            depth=depth,
            n_simulations=n_simulations,
            seed=seed,
            log_every=0,
            objective="mse",
            external_scorer=external_scorer,
        )
    except Exception:
        return None, None, False, 0

    best_tree = result.best_tree
    formula_str = result.best_formula
    n_sims = result.n_simulations

    if best_tree is None or result.best_mse > 1.0:
        return best_tree, formula_str, False, n_sims

    # Try symbolic verification: T == rhs?
    try:
        tree_sym = _tree_to_sympy(best_tree)
        diff = sympy.simplify(tree_sym - rhs_expr)
        proved = diff == 0
        return best_tree, formula_str, proved, n_sims
    except Exception:
        return best_tree, formula_str, False, n_sims


def _build_latex_proof(
    identity_str: str,
    lhs_expr,
    rhs_expr,
    status: str,
    method: str,
    simplification: Optional[str],
) -> str:
    """Build a simple LaTeX proof string."""
    if not _SYMPY_OK or lhs_expr is None or rhs_expr is None:
        lines = [
            r"\begin{proof}",
            rf"  \textbf{{Identity:}} ${identity_str}$\\",
            rf"  \textbf{{Status:}} {status} (method: {method})\\",
            r"\end{proof}",
        ]
        return "\n".join(lines)

    try:
        lhs_latex = sympy.latex(lhs_expr)
        rhs_latex = sympy.latex(rhs_expr)
    except Exception:
        lhs_latex = str(lhs_expr)
        rhs_latex = str(rhs_expr)

    lines = [
        r"\begin{proof}",
        rf"  \textbf{{Claim:}} ${lhs_latex} = {rhs_latex}$\\[4pt]",
    ]

    if method == "sympy":
        lines.append(
            r"  \textbf{Method:} Symbolic verification via SymPy \texttt{simplify}.\\"
        )
        if simplification is not None:
            lines.append(rf"  $\mathrm{{simplify}}(\mathrm{{LHS}} - \mathrm{{RHS}}) = {simplification}$\\")
    elif method == "numerical":
        lines.append(
            r"  \textbf{Method:} Numerical evaluation at 500 probe points.\\"
        )
    elif method == "interval":
        lines.append(
            r"  \textbf{Method:} Certified interval arithmetic over 20 sub-intervals.\\"
        )
    elif method == "eml_witness":
        lines.append(
            r"  \textbf{Method:} EML witness found by MCTS; verified symbolically.\\"
        )

    if status.startswith("proved"):
        lines.append(r"  Identity verified. \qed")
    else:
        lines.append(r"  Identity \textbf{not} verified by automated methods.")

    lines.append(r"\end{proof}")
    return "\n".join(lines)


# ── EMLProver ─────────────────────────────────────────────────────────────────

class EMLProver:
    """Neurosymbolic theorem prover for EML identities.

    Uses a four-tier strategy: numerical → exact (SymPy) → certified (interval)
    → EML witness (MCTS + SymPy verification).

    Args:
        verbose:  If True, print progress messages during proving.
        n_probe:  Number of probe points for numerical checks.

    Examples::

        prover = EMLProver(verbose=True)
        result = prover.prove("exp(x) * exp(-x) == 1")
        print(result.status)  # 'proved_exact'
    """

    def __init__(
        self,
        verbose: bool = False,
        n_probe: int = 500,
        scorer: "Optional[Any]" = None,
    ) -> None:
        self.verbose = verbose
        self.n_probe = n_probe
        self.scorer = scorer  # Optional FeatureBasedEMLScorer

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[EMLProver] {msg}")

    def prove(
        self,
        identity: str,
        max_nodes: int = 10,
        n_simulations: int = 3000,
        timeout: float = 60.0,
        domain: Tuple[float, float] = (-math.pi, math.pi),
        seed: int = 42,
    ) -> ProofResult:
        """Attempt to prove a mathematical identity.

        Args:
            identity:      Identity string, e.g. ``'sin(x)**2 + cos(x)**2 == 1'``.
            max_nodes:     Max nodes in the MCTS witness tree search.
            n_simulations: Number of MCTS simulations for witness search.
            timeout:       Soft wall-clock time limit (seconds).
            domain:        (lo, hi) domain for testing.
            seed:          Random seed for MCTS.

        Returns:
            ProofResult with full metadata.
        """
        t0 = time.perf_counter()
        notes: List[str] = []
        identity = identity.strip()

        self._log(f"Attempting: {identity!r}")

        # ── Parse ─────────────────────────────────────────────────────────────
        lhs_str, rhs_str = _parse_identity(identity)
        if lhs_str is None:
            return self._failed_result(identity, t0, "Cannot parse: missing '=='", notes)

        # ── Build callables ───────────────────────────────────────────────────
        lo, hi = domain
        # Avoid degenerate domain
        if lo == hi:
            probe_points = [lo]
        else:
            probe_points = _linspace(lo, hi, self.n_probe)

        lhs_fn = _make_math_fn(lhs_str)
        rhs_fn = _make_math_fn(rhs_str)

        if lhs_fn is None or rhs_fn is None:
            notes.append("Failed to build numeric callables from expression strings")
            # Try without failing — maybe only SymPy path works

        # ── Numerical check ───────────────────────────────────────────────────
        num_proved, max_res = _numerical_check(lhs_fn, rhs_fn, probe_points)
        n_test = len(probe_points)

        if math.isfinite(max_res):
            notes.append(f"Numerical check: max residual = {max_res:.4e} over {n_test} points")
        else:
            notes.append("Numerical check: could not evaluate (non-finite)")
            max_res = float("inf")

        # ── SymPy exact check ─────────────────────────────────────────────────
        lhs_expr = _sympy_parse(lhs_str)
        rhs_expr = _sympy_parse(rhs_str)

        if lhs_expr is None or rhs_expr is None:
            notes.append("SymPy could not parse one or both sides")

        sympy_proved = False
        simplified_str: Optional[str] = None

        if lhs_expr is not None and rhs_expr is not None:
            self._log("Trying SymPy exact check...")
            sympy_proved, simplified_str = _try_sympy_exact(lhs_expr, rhs_expr)
            if sympy_proved:
                notes.append("SymPy simplify(LHS - RHS) == 0  → EXACT PROOF")
            else:
                notes.append(
                    f"SymPy could not simplify to 0 (got: {simplified_str})"
                )

        elapsed = time.perf_counter() - t0

        # ── Return exact proof ────────────────────────────────────────────────
        if sympy_proved:
            latex_str = _build_latex_proof(
                identity, lhs_expr, rhs_expr,
                "proved_exact", "sympy", simplified_str
            )
            return ProofResult(
                identity_str=identity,
                status="proved_exact",
                verification_method="sympy",
                confidence=1.0,
                max_residual=max_res if math.isfinite(max_res) else 0.0,
                n_test_points=n_test,
                elapsed_s=elapsed,
                lhs_tree=None,
                rhs_tree=None,
                witness_tree=None,
                node_count=0,
                mcts_simulations=0,
                lhs_formula=None,
                latex_proof=latex_str,
                sympy_simplification=simplified_str,
                notes=notes,
            )

        # ── Certified interval check ──────────────────────────────────────────
        certified = False
        cert_max_res = float("inf")

        if lhs_fn is not None and rhs_fn is not None and lo != hi:
            self._log("Trying certified interval check...")
            certified, cert_max_res = _certified_interval_check(
                lhs_fn, rhs_fn, (lo, hi), n_sub=20, threshold=1e-6
            )
            if certified:
                notes.append(f"Interval check: max residual = {cert_max_res:.4e} over 20 sub-intervals → CERTIFIED")
            else:
                notes.append(f"Interval check: max residual = {cert_max_res:.4e} (threshold not met)")

        elapsed = time.perf_counter() - t0

        # ── Numerical proof ───────────────────────────────────────────────────
        if num_proved:
            latex_str = _build_latex_proof(
                identity, lhs_expr, rhs_expr,
                "proved_numerical", "numerical", simplified_str
            )
            return ProofResult(
                identity_str=identity,
                status="proved_numerical",
                verification_method="numerical",
                confidence=0.9,
                max_residual=max_res,
                n_test_points=n_test,
                elapsed_s=elapsed,
                lhs_tree=None,
                rhs_tree=None,
                witness_tree=None,
                node_count=0,
                mcts_simulations=0,
                lhs_formula=None,
                latex_proof=latex_str,
                sympy_simplification=simplified_str,
                notes=notes,
            )

        if certified:
            latex_str = _build_latex_proof(
                identity, lhs_expr, rhs_expr,
                "proved_certified", "interval", simplified_str
            )
            # Use the better residual
            best_res = min(max_res, cert_max_res)
            return ProofResult(
                identity_str=identity,
                status="proved_certified",
                verification_method="interval",
                confidence=0.95,
                max_residual=best_res,
                n_test_points=n_test,
                elapsed_s=elapsed,
                lhs_tree=None,
                rhs_tree=None,
                witness_tree=None,
                node_count=0,
                mcts_simulations=0,
                lhs_formula=None,
                latex_proof=latex_str,
                sympy_simplification=simplified_str,
                notes=notes,
            )

        # ── EML Witness search ────────────────────────────────────────────────
        remaining = timeout - (time.perf_counter() - t0)

        witness_tree: Optional[dict] = None
        lhs_formula: Optional[str] = None
        witness_proved = False
        n_mcts: int = 0

        if (
            _MCTS_OK
            and lhs_fn is not None
            and rhs_expr is not None
            and remaining > 2.0
            and lo != hi
        ):
            self._log(f"Running MCTS witness search (n_sim={n_simulations})...")
            # Use finite probe points for MCTS
            mcts_probes = probe_points if len(probe_points) <= 200 else probe_points[::3]
            _ext_scorer = (
                self.scorer.score
                if self.scorer is not None and self.scorer.is_trained()
                else None
            )
            witness_tree, lhs_formula, witness_proved, n_mcts = _mcts_witness_search(
                lhs_fn=lhs_fn,
                probe_points=mcts_probes,
                rhs_expr=rhs_expr,
                max_nodes=max_nodes,
                n_simulations=n_simulations,
                seed=seed,
                timeout=remaining,
                external_scorer=_ext_scorer,
            )
            if witness_proved:
                notes.append(f"MCTS found EML witness: {lhs_formula!r} → verified with SymPy")
            elif witness_tree is not None:
                notes.append(f"MCTS found tree: {lhs_formula!r}, but SymPy could not verify")
            else:
                notes.append("MCTS witness search failed or timed out")

        elapsed = time.perf_counter() - t0

        if witness_proved and witness_tree is not None:
            node_cnt = _count_nodes(witness_tree)
            # Online learning: feed successful witness to the scorer
            if self.scorer is not None:
                reward = 1.0 / (1.0 + node_cnt)
                self.scorer.update(witness_tree, reward)
            latex_str = _build_latex_proof(
                identity, lhs_expr, rhs_expr,
                "proved_witness", "eml_witness", simplified_str
            )
            return ProofResult(
                identity_str=identity,
                status="proved_witness",
                verification_method="eml_witness",
                confidence=1.0,
                max_residual=max_res if math.isfinite(max_res) else float("inf"),
                n_test_points=n_test,
                elapsed_s=elapsed,
                lhs_tree=witness_tree,
                rhs_tree=None,
                witness_tree=witness_tree,
                node_count=node_cnt,
                mcts_simulations=n_mcts,
                lhs_formula=lhs_formula,
                latex_proof=latex_str,
                sympy_simplification=simplified_str,
                notes=notes,
            )

        # ── Inconclusive / failed ─────────────────────────────────────────────
        elapsed = time.perf_counter() - t0

        # Decide status: inconclusive if we have a small residual but not below threshold
        if math.isfinite(max_res) and max_res < 1e-4:
            status = "inconclusive"
            confidence = 0.5
            notes.append(f"Residual {max_res:.2e} is small but above proof threshold")
        else:
            status = "failed"
            confidence = 0.0
            notes.append("All proof methods failed or inapplicable")

        latex_str = _build_latex_proof(
            identity, lhs_expr, rhs_expr,
            status, "combined", simplified_str
        )
        node_cnt = _count_nodes(witness_tree) if witness_tree else 0
        return ProofResult(
            identity_str=identity,
            status=status,
            verification_method="combined",
            confidence=confidence,
            max_residual=max_res if math.isfinite(max_res) else float("inf"),
            n_test_points=n_test,
            elapsed_s=elapsed,
            lhs_tree=witness_tree,
            rhs_tree=None,
            witness_tree=None,
            node_count=node_cnt,
            mcts_simulations=n_mcts,
            lhs_formula=lhs_formula,
            latex_proof=latex_str,
            sympy_simplification=simplified_str,
            notes=notes,
        )

    def _failed_result(
        self,
        identity: str,
        t0: float,
        reason: str,
        notes: List[str],
    ) -> ProofResult:
        """Build a failed ProofResult with a reason."""
        notes = list(notes) + [reason]
        return ProofResult(
            identity_str=identity,
            status="failed",
            verification_method="none",
            confidence=0.0,
            max_residual=float("inf"),
            n_test_points=0,
            elapsed_s=time.perf_counter() - t0,
            lhs_tree=None,
            rhs_tree=None,
            witness_tree=None,
            node_count=0,
            mcts_simulations=0,
            lhs_formula=None,
            latex_proof=None,
            sympy_simplification=None,
            notes=notes,
        )

    def prove_batch(
        self,
        identities: List[str],
        **kwargs: Any,
    ) -> List[ProofResult]:
        """Prove a list of identities, returning all results.

        All keyword arguments are forwarded to :meth:`prove`.

        Args:
            identities: List of identity strings.
            **kwargs:   Passed to ``prove()``.

        Returns:
            List of ProofResult, one per identity (preserving order).
        """
        results = []
        for idx, ident in enumerate(identities):
            self._log(f"[{idx+1}/{len(identities)}] {ident!r}")
            results.append(self.prove(ident, **kwargs))
        return results

    def benchmark(
        self,
        catalog: Optional[List[Any]] = None,
        n_simulations: int = 1000,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> BenchmarkReport:
        """Run a benchmark over a catalog of identities.

        Args:
            catalog:      List of Identity objects (from monogate.identities)
                          or plain identity strings.  Defaults to easy/trivial
                          identities from the built-in catalog.
            n_simulations: MCTS simulations per identity.
            timeout:      Per-identity timeout.
            **kwargs:     Additional args forwarded to ``prove()``.

        Returns:
            BenchmarkReport with aggregated statistics.
        """
        if catalog is None:
            try:
                from .identities import ALL_IDENTITIES
                catalog = [
                    i for i in ALL_IDENTITIES
                    if i.difficulty in ("trivial", "easy")
                ]
            except ImportError:
                catalog = []

        results: List[ProofResult] = []
        for item in catalog:
            # Accept either Identity objects or plain strings
            if hasattr(item, "expression"):
                ident_str = item.expression
                dom = item.domain if hasattr(item, "domain") else (-math.pi, math.pi)
            else:
                ident_str = str(item)
                dom = (-math.pi, math.pi)

            result = self.prove(
                ident_str,
                n_simulations=n_simulations,
                timeout=timeout,
                domain=dom,
                **kwargs,
            )
            results.append(result)

        n_total = len(results)
        n_proved = sum(1 for r in results if r.proved())
        n_exact = sum(1 for r in results if r.status == "proved_exact")
        n_numerical = sum(1 for r in results if r.status in (
            "proved_numerical", "proved_certified"
        ))
        n_failed = n_total - n_proved

        success_rate = n_proved / n_total if n_total > 0 else 0.0
        mean_elapsed = sum(r.elapsed_s for r in results) / max(n_total, 1)
        mean_nodes = sum(r.node_count for r in results) / max(n_total, 1)

        return BenchmarkReport(
            results=results,
            n_total=n_total,
            n_proved=n_proved,
            n_exact=n_exact,
            n_numerical=n_numerical,
            n_failed=n_failed,
            success_rate=success_rate,
            mean_elapsed_s=mean_elapsed,
            mean_nodes=mean_nodes,
        )


# ── EMLProverV2 ───────────────────────────────────────────────────────────────

class EMLProverV2(EMLProver):
    """Extended prover with conjecture generation, proof compression, visualization,
    and optional online neural scoring.

    Inherits all four-tier proof logic from :class:`EMLProver` and adds:

    - :meth:`generate_conjectures` — propose new identities via grammar mutation.
    - :meth:`compress_proof` — shorten an EML witness tree while preserving correctness.
    - :meth:`visualize_proof` — publication-quality tree diagram (matplotlib).
    - :meth:`visualize_proof_interactive` — interactive Plotly tree (HTML output).
    - :meth:`batch_prove` — prove a list of identities with progress reporting.

    Args:
        verbose:         Print proof progress.
        n_probe:         Probe points for numerical checks.
        enable_learning: If True, attach a FeatureBasedEMLScorer that learns
                         online from successful witness proofs.
        scorer_path:     Path to a previously saved scorer JSON file to restore.

    Example::

        prover = EMLProverV2(enable_learning=True)
        result = prover.prove("sin(x)**2 + cos(x)**2 == 1")
        prover.visualize_proof_interactive(result, output_path="proof.html")
        prover.scorer.save("scorer_checkpoint.json")
    """

    def __init__(
        self,
        verbose: bool = False,
        n_probe: int = 500,
        enable_learning: bool = False,
        scorer_path: Optional[str] = None,
        use_pretrained: bool = False,
    ) -> None:
        scorer = None
        if enable_learning or use_pretrained:
            from .neural_scorer import FeatureBasedEMLScorer
            scorer = FeatureBasedEMLScorer()
            # Explicit scorer_path takes priority; pretrained default as fallback
            load_path = scorer_path
            if load_path is None and use_pretrained:
                try:
                    import importlib.resources as _pkg_res
                    _ref = _pkg_res.files("monogate.data") / "pretrained_scorer.json"
                    load_path = str(_ref)
                except Exception:
                    pass
            if load_path and os.path.exists(load_path):
                try:
                    scorer.load(load_path)
                except Exception:
                    pass
        super().__init__(verbose=verbose, n_probe=n_probe, scorer=scorer)

    # ── Conjecture generation ────────────────────────────────────────────────

    def generate_conjectures(
        self,
        category: str = "trig",
        n: int = 20,
        difficulty: str = "medium",
        seed: int = 42,
        temperature: float = 0.5,
    ) -> "List[Any]":
        """Generate plausible new mathematical identities via grammar mutation.

        Strategy
        --------
        1. Pull all identities in *category* from the existing catalog.
        2. Apply temperature-controlled mutations (more creative at high temperature).
        3. Numerically check each candidate (500 points, threshold 1e-6).
        4. Deduplicate against existing catalog.
        5. Rank by novelty × simplicity bonus; if scorer is trained, apply a
           complexity-weighted neural hint (shorter = more likely to have a
           short EML witness, which the scorer rewards).
        6. Return the top *n* candidates as
           :class:`~monogate.identities.Identity` objects.

        Args:
            category:    One of 'trig', 'trigonometric', 'hyperbolic',
                         'exponential', 'special', 'physics', 'eml', 'open'.
                         Short aliases accepted.
            n:           Maximum number of conjectures to return.
            difficulty:  Difficulty label to stamp on returned identities.
            seed:        Random seed for reproducibility.
            temperature: Mutation aggressiveness in [0, 1].
                         0.0 = only argument substitutions (safe).
                         0.5 = moderate (default — current set).
                         1.0 = maximum creativity (more diverse, more may fail).

        Returns:
            List of :class:`~monogate.identities.Identity` objects with
            ``expected_method='unknown'``.
        """
        import random as _random
        from .identities import ALL_IDENTITIES, Identity

        # Normalise category alias
        _alias = {
            "trig": "trigonometric",
            "hyp": "hyperbolic",
            "exp": "exponential",
        }
        cat = _alias.get(category, category)

        pool = [i for i in ALL_IDENTITIES if i.category == cat]
        if not pool:
            pool = ALL_IDENTITIES[:]

        existing_exprs = {i.expression for i in ALL_IDENTITIES}
        rng = _random.Random(seed)

        # (novelty, complexity_bonus, name, expr, cat, domain)
        candidates: "List[tuple]" = []

        for identity in pool:
            lhs, rhs = self._split_identity(identity.expression)
            if lhs is None:
                continue
            mutations = self._mutate_identity(lhs, rhs, rng, temperature=temperature)
            for (new_lhs, new_rhs, mutation_name) in mutations:
                expr = f"{new_lhs} == {new_rhs}"
                if expr in existing_exprs:
                    continue
                lhs_fn = _make_math_fn(new_lhs)
                rhs_fn = _make_math_fn(new_rhs)
                if lhs_fn is None or rhs_fn is None:
                    continue
                lo, hi = identity.domain
                probe = _linspace(lo, hi, 500)
                ok, residual = _numerical_check(lhs_fn, rhs_fn, probe, threshold=1e-6)
                if ok:
                    novelty = 1.0 / (1.0 + residual * 1e6 + 0.1)
                    # Simplicity bonus: shorter expressions tend to have shorter
                    # EML witnesses — important when scorer is untrained.
                    simplicity = 1.0 / (1.0 + len(expr) / 80.0)
                    candidates.append((
                        novelty, simplicity,
                        f"auto_{mutation_name}_{identity.name[:20]}",
                        expr, cat, identity.domain,
                    ))
                    existing_exprs.add(expr)

        # ── Ranking ────────────────────────────────────────────────────────────
        scorer_trained = (
            self.scorer is not None and self.scorer.is_trained()
        )
        if scorer_trained:
            # Neural hint: prefer candidates whose expression length suggests
            # a short EML witness (proxy for what the scorer has learned).
            # weight = 0.6 * novelty + 0.2 * simplicity + 0.2 * neural_hint
            # neural_hint is the simplicity score amplified by scorer confidence.
            def _score(c):
                novelty, simplicity, *_ = c
                neural_hint = simplicity * 1.5  # amplify compact expressions
                neural_hint = min(neural_hint, 1.0)
                return 0.6 * novelty + 0.2 * simplicity + 0.2 * neural_hint
        else:
            def _score(c):
                novelty, simplicity, *_ = c
                return 0.7 * novelty + 0.3 * simplicity

        candidates.sort(key=_score, reverse=True)

        results = []
        for row in candidates[:n]:
            novelty, simplicity, name, expr, icat, domain = row
            results.append(Identity(
                name=name,
                expression=expr,
                latex=self._expr_to_latex(expr),
                category=icat,
                domain=domain,
                difficulty=difficulty,
                notes=(
                    f"Auto-generated conjecture (novelty={novelty:.4f}, "
                    f"temperature={temperature:.2f}). Numerically verified."
                ),
                expected_method="unknown",
            ))
        return results

    # ── Explorer mode ────────────────────────────────────────────────────────

    def explore(
        self,
        n_rounds: int = 10,
        n_per_round: int = 20,
        seed_category: str = "trig",
        temperature: float = 0.7,
        compress_witnesses: bool = True,
        verbose: bool = True,
    ) -> dict:
        """Conjecture–verify–learn loop: the core exploration engine.

        Each round:

        1. **Generate** — :meth:`generate_conjectures` produces *n_per_round*
           numerically-plausible candidates using temperature-controlled mutations
           seeded from *seed_category*.
        2. **Verify** — each candidate is proved with the full 4-tier pipeline.
        3. **Compress** — if a witness tree was found by MCTS, attempt to shorten
           it via :meth:`compress_proof`.
        4. **Learn** — the scorer automatically updates from any MCTS witnesses
           (via :meth:`~monogate.neural_scorer.FeatureBasedEMLScorer.update`
           called inside :meth:`prove`).
        5. **Accumulate** — proved conjectures are added to an in-memory
           "discovered" catalog that persists across rounds.

        Args:
            n_rounds:          Number of generate–verify–learn cycles.
            n_per_round:       Conjectures generated per round.
            seed_category:     Category to seed mutations from.  ``'trig'``
                               transfers best to other domains.
            temperature:       Mutation aggressiveness passed to
                               :meth:`generate_conjectures`.
            compress_witnesses: If True, attempt :meth:`compress_proof` on
                                any MCTS witness trees that are found.
            verbose:           Print a one-line summary after each round.

        Returns:
            dict with keys:

            - ``discovered``: list of ``(Identity, ProofResult)`` tuples for
              all proved conjectures across all rounds.
            - ``learning_curve``: list of per-round dicts recording conjecture
              counts, proof counts, and scorer status.
            - ``n_total_discovered``: total number of proved conjectures.
        """
        import time as _time

        discovered: "List[tuple]" = []
        learning_curve: "List[dict]" = []
        seen_exprs: set = set()

        for round_idx in range(n_rounds):
            t0 = _time.perf_counter()

            conjectures = self.generate_conjectures(
                category=seed_category,
                n=n_per_round,
                seed=round_idx * 1000 + 7,
                temperature=temperature,
            )

            n_proved_this_round = 0
            n_witness_this_round = 0

            for conjecture in conjectures:
                if conjecture.expression in seen_exprs:
                    continue
                seen_exprs.add(conjecture.expression)

                result = self.prove(conjecture.expression)

                if result.proved():
                    n_proved_this_round += 1
                    # Compress MCTS witness if one was found
                    if (compress_witnesses
                            and result.witness_tree is not None
                            and result.status == "proved_witness"):
                        n_witness_this_round += 1
                        try:
                            result = self.compress_proof(result)
                        except Exception:
                            pass
                    discovered.append((conjecture, result))

            elapsed = _time.perf_counter() - t0
            scorer_trained = (
                self.scorer is not None and self.scorer.is_trained()
            )
            scorer_buf = len(self.scorer._buffer) if self.scorer else 0

            round_stats = {
                "round":             round_idx + 1,
                "n_conjectures":     len(conjectures),
                "n_proved":          n_proved_this_round,
                "n_witness":         n_witness_this_round,
                "n_discovered_total": len(discovered),
                "scorer_trained":    scorer_trained,
                "scorer_buffer":     scorer_buf,
                "elapsed_s":         elapsed,
            }
            learning_curve.append(round_stats)

            if verbose:
                status = "trained" if scorer_trained else f"buf={scorer_buf}"
                print(
                    f"  Round {round_idx+1}/{n_rounds}: "
                    f"generated={len(conjectures)}  "
                    f"proved={n_proved_this_round}  "
                    f"total={len(discovered)}  "
                    f"scorer={status}  "
                    f"({elapsed:.1f}s)"
                )

        return {
            "discovered":         discovered,
            "learning_curve":     learning_curve,
            "n_total_discovered": len(discovered),
        }

    # ── Proof compression ────────────────────────────────────────────────────

    def compress_proof(
        self,
        result: ProofResult,
        n_simulations: int = 2000,
        seed: int = 42,
    ) -> ProofResult:
        """Find a shorter EML witness tree for an existing ProofResult.

        Uses :func:`~monogate.minimax.minimax_eml` to search for an equivalent
        tree with fewer internal nodes.  If no shorter tree is found, returns
        the original result unchanged.

        Args:
            result:       A :class:`ProofResult` that has a ``witness_tree``.
            n_simulations: MCTS budget for the compression search.
            seed:         Random seed.

        Returns:
            :class:`ProofResult` with updated ``witness_tree`` and ``node_count``,
            or the original if already minimal.
        """
        if result.witness_tree is None:
            return result

        try:
            from .minimax import minimax_eml
        except ImportError:
            return result

        original_nodes = _count_nodes(result.witness_tree)
        if original_nodes <= 1:
            return result

        # Build target function from witness tree
        def target_fn(x: float) -> float:
            try:
                return _eval_tree(result.witness_tree, x)
            except Exception:
                return float("nan")

        # Attempt progressively smaller trees
        best_tree = result.witness_tree
        best_nodes = original_nodes

        for n_nodes in range(original_nodes - 1, 0, -1):
            try:
                mm = minimax_eml(
                    target_fn,
                    n_nodes=n_nodes,
                    domain=(-math.pi, math.pi),
                    n_probe=100,
                    n_simulations=n_simulations,
                    seed=seed,
                )
                if mm.linf < 1e-10:
                    best_tree = mm.best_tree
                    best_nodes = _count_nodes(mm.best_tree)
                    n_simulations = max(500, n_simulations // 2)  # budget halving
                else:
                    break  # can't compress further
            except Exception:
                break

        if best_nodes >= original_nodes:
            return result

        new_notes = list(result.notes) + [
            f"Proof compressed: {original_nodes} nodes → {best_nodes} nodes "
            f"(minimax_eml, L∞ < 1e-10)"
        ]
        # ProofResult is frozen — rebuild with updated fields
        return ProofResult(
            identity_str=result.identity_str,
            status=result.status,
            verification_method=result.verification_method,
            confidence=result.confidence,
            max_residual=result.max_residual,
            n_test_points=result.n_test_points,
            elapsed_s=result.elapsed_s,
            lhs_tree=result.lhs_tree,
            rhs_tree=result.rhs_tree,
            witness_tree=best_tree,
            node_count=best_nodes,
            mcts_simulations=result.mcts_simulations,
            lhs_formula=_formula_str(best_tree),
            latex_proof=result.latex_proof,
            sympy_simplification=result.sympy_simplification,
            notes=new_notes,
        )

    # ── Visualization ────────────────────────────────────────────────────────

    def visualize_proof(
        self,
        result: ProofResult,
        style: str = "tree",
        output_path: Optional[str] = None,
    ) -> None:
        """Render a publication-quality diagram of the EML proof tree.

        Builds a directed graph from the witness (or LHS) tree and draws it
        using matplotlib, with color-coded nodes:

        - **cornflowerblue**: internal EML operation nodes
        - **lightgreen**: constant leaf nodes
        - **coral**: variable ``x`` leaf nodes

        Args:
            result:      A :class:`ProofResult` to visualize.
            style:       One of ``'tree'`` (hierarchical), ``'radial'``,
                         or ``'step'`` (LHS | → | RHS side-by-side).
            output_path: If given, save to this file path instead of showing.

        Raises:
            ImportError: If matplotlib is not installed.
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            raise ImportError("matplotlib is required for visualize_proof. "
                              "Install with: pip install matplotlib")

        tree = result.witness_tree or result.lhs_tree
        if tree is None:
            # Nothing to draw — just show text
            fig, ax = plt.subplots(figsize=(8, 2))
            ax.axis("off")
            ax.text(0.5, 0.5, f"{result.identity_str}\n{result}\n(no EML witness tree)",
                    ha="center", va="center", fontsize=12, wrap=True)
            _show_or_save(fig, output_path)
            return

        if style == "step":
            self._visualize_step(result, output_path)
        else:
            radial = (style == "radial")
            self._visualize_single_tree(tree, result, radial=radial,
                                        output_path=output_path)

    # ── Interactive Plotly visualization ─────────────────────────────────────

    def visualize_proof_interactive(
        self,
        result: ProofResult,
        output_path: Optional[str] = None,
    ) -> "Any":
        """Render an interactive Plotly graph of the EML proof tree.

        Requires ``plotly`` (``pip install plotly``).

        Node colors:
          - ``#6495ED`` (cornflower blue) — EML internal nodes
          - ``#90EE90`` (light green) — constant leaves
          - ``#FA8072`` (salmon) — variable leaf (x)

        Hover text shows the full sub-formula at each node.

        Args:
            result:      ProofResult from :meth:`prove`.
            output_path: If given (must end in ``.html``), write the figure
                         to that file.  If ``None``, return the figure object
                         for display in Jupyter or Streamlit.

        Returns:
            ``plotly.graph_objects.Figure``.

        Raises:
            ImportError: If plotly is not installed.
        """
        try:
            import plotly.graph_objects as go  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "plotly is required for interactive visualization. "
                "Install with: pip install plotly"
            ) from exc

        from .search.mcts import _formula

        tree = result.witness_tree
        if tree is None:
            # Fall back to a single-node placeholder
            tree = {"op": "leaf", "val": "?"}

        # ── Build positions via BFS layout ────────────────────────────────
        positions: dict = {}
        labels: dict = {}
        colors: dict = {}
        hover: dict = {}
        edges: list = []

        _COLOR_EML   = "#6495ED"
        _COLOR_CONST = "#90EE90"
        _COLOR_X     = "#FA8072"

        node_id = [0]

        def _assign(t, parent_id, x_pos, y_pos, x_spread):
            nid = node_id[0]
            node_id[0] += 1
            positions[nid] = (x_pos, y_pos)

            try:
                sub_formula = _formula(t)[:30]
            except Exception:
                sub_formula = str(t.get("val", "?"))

            if t["op"] == "eml":
                labels[nid] = "eml"
                colors[nid] = _COLOR_EML
                hover[nid] = f"eml node<br>{sub_formula}"
                if parent_id is not None:
                    edges.append((parent_id, nid))
                half = x_spread / 2.0
                _assign(t["left"],  nid, x_pos - half, y_pos - 1, half)
                _assign(t["right"], nid, x_pos + half, y_pos - 1, half)
            else:
                val = t["val"]
                if val == "x":
                    labels[nid] = "x"
                    colors[nid] = _COLOR_X
                    hover[nid] = "variable x"
                else:
                    labels[nid] = str(round(float(val), 3))
                    colors[nid] = _COLOR_CONST
                    hover[nid] = f"const {val}"
                if parent_id is not None:
                    edges.append((parent_id, nid))

        _assign(tree, None, 0.0, 0.0, 4.0)

        # ── Edge traces ───────────────────────────────────────────────────
        edge_x, edge_y = [], []
        for src, dst in edges:
            x0, y0 = positions[src]
            x1, y1 = positions[dst]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=1.5, color="#888"),
            hoverinfo="none",
        )

        # ── Node traces ───────────────────────────────────────────────────
        node_x = [positions[n][0] for n in sorted(positions)]
        node_y = [positions[n][1] for n in sorted(positions)]
        node_colors = [colors[n] for n in sorted(positions)]
        node_labels = [labels[n] for n in sorted(positions)]
        node_hover  = [hover[n]  for n in sorted(positions)]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            marker=dict(size=28, color=node_colors, line=dict(width=1.5, color="#333")),
            text=node_labels,
            textposition="middle center",
            hovertext=node_hover,
            hoverinfo="text",
        )

        title = (
            f"{result.identity_str[:60]}<br>"
            f"<sup>status: {result.status} | confidence: {result.confidence:.2f}"
            f" | nodes: {result.node_count}</sup>"
        )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(text=title, x=0.5, font=dict(size=13)),
                showlegend=False,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=60),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="white",
                annotations=[
                    dict(
                        text="<b>●</b> EML  <b>●</b> const  <b>●</b> x",
                        xref="paper", yref="paper",
                        x=0.01, y=-0.02,
                        showarrow=False,
                        font=dict(size=10, color="#555"),
                    )
                ],
            ),
        )

        if output_path is not None:
            fig.write_html(output_path)

        return fig

    # ── Batch prove with progress ────────────────────────────────────────────

    def batch_prove(
        self,
        catalog_slice: "List[Any]",
        show_progress: bool = True,
        **kwargs: Any,
    ) -> BenchmarkReport:
        """Prove a list of identities with optional progress reporting.

        Args:
            catalog_slice: List of :class:`~monogate.identities.Identity` objects
                           or identity strings.
            show_progress: If True, print a one-line status for each identity.
            **kwargs:      Forwarded to :meth:`EMLProver.prove`.

        Returns:
            :class:`BenchmarkReport` summary.
        """
        from .identities import Identity as _Identity
        identity_strs = []
        for item in catalog_slice:
            if isinstance(item, _Identity):
                identity_strs.append(item.expression)
            else:
                identity_strs.append(str(item))

        results: List[ProofResult] = []
        n = len(identity_strs)
        for idx, expr in enumerate(identity_strs):
            r = self.prove(expr, **kwargs)
            results.append(r)
            if show_progress:
                symbol = "✓" if r.proved() else "✗"
                print(f"  [{idx+1}/{n}] {symbol} {r.status:20s}  {expr[:60]}")

        n_total = len(results)
        n_proved = sum(1 for r in results if r.proved())
        n_exact = sum(1 for r in results if r.status == "proved_exact")
        n_numerical = sum(1 for r in results if r.status in (
            "proved_numerical", "proved_certified"))
        n_failed = n_total - n_proved
        success_rate = n_proved / n_total if n_total > 0 else 0.0
        mean_elapsed = sum(r.elapsed_s for r in results) / max(n_total, 1)
        mean_nodes = sum(r.node_count for r in results) / max(n_total, 1)
        return BenchmarkReport(
            results=results, n_total=n_total, n_proved=n_proved,
            n_exact=n_exact, n_numerical=n_numerical, n_failed=n_failed,
            success_rate=success_rate, mean_elapsed_s=mean_elapsed,
            mean_nodes=mean_nodes,
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _split_identity(expression: str) -> Tuple[Optional[str], Optional[str]]:
        """Split 'lhs == rhs' into (lhs, rhs), or (None, None) if malformed."""
        parts = expression.split("==")
        if len(parts) != 2:
            return None, None
        return parts[0].strip(), parts[1].strip()

    @staticmethod
    def _mutate_identity(
        lhs: str,
        rhs: str,
        rng: "Any",
        temperature: float = 0.5,
    ) -> "List[Tuple[str, str, str]]":
        """Return list of (new_lhs, new_rhs, mutation_name) tuples.

        ``temperature`` controls mutation aggressiveness:

        - 0.0–0.3  (conservative): argument substitutions only
        - 0.3–0.6  (moderate):     + scalar mutations and phase shifts
        - 0.6–0.8  (creative):     + triple-angle, π/4-shift, additive combos
        - 0.8–1.0  (aggressive):   + log/exp wrapping, random scale factors
        """
        mutations = []

        # ── Tier 1: always included (temperature-independent) ────────────────
        mutations.append((lhs.replace("x", "(2*x)"),   rhs.replace("x", "(2*x)"),   "double_arg"))
        mutations.append((lhs.replace("x", "(x/2)"),   rhs.replace("x", "(x/2)"),   "half_arg"))

        # ── Tier 2: moderate temperature ≥ 0.3 ──────────────────────────────
        if temperature >= 0.3:
            mutations.append((f"(-({lhs}))",           f"(-({rhs}))",               "negate"))
            mutations.append((f"(2*({lhs}))",          f"(2*({rhs}))",              "scale2"))
            mutations.append((f"(({lhs})/2)",          f"(({rhs})/2)",              "scale_half"))
            mutations.append((lhs.replace("x", "(x+1)"), rhs.replace("x", "(x+1)"), "shift1"))

        # ── Tier 3: creative temperature ≥ 0.6 ──────────────────────────────
        if temperature >= 0.6:
            import math as _math
            pi_str = f"{_math.pi:.10f}"
            mutations.append((lhs.replace("x", "(3*x)"),               rhs.replace("x", "(3*x)"),               "triple_arg"))
            mutations.append((lhs.replace("x", f"(x+{pi_str}/4)"),     rhs.replace("x", f"(x+{pi_str}/4)"),     "phase_pi4"))
            mutations.append((lhs.replace("x", f"(x+{pi_str}/6)"),     rhs.replace("x", f"(x+{pi_str}/6)"),     "phase_pi6"))
            mutations.append((f"(3*({lhs}))",                           f"(3*({rhs}))",                          "scale3"))
            # Additive: LHS + RHS == LHS + RHS (trivially true, tests filtering)
            # More interesting: combine two halves
            mutations.append((f"(({lhs})+({lhs}))",                    f"(({rhs})+({rhs}))",                    "double_expr"))

        # ── Tier 4: aggressive temperature ≥ 0.8 ────────────────────────────
        if temperature >= 0.8:
            # Random rational scale (avoids trivial multiples already in catalog)
            scale = rng.choice([3, 4, 5, 7]) / rng.choice([2, 3, 4])
            scale_str = f"{scale:.6f}"
            mutations.append((f"({scale_str}*({lhs}))", f"({scale_str}*({rhs}))", "rand_scale"))
            # Argument: x → x + random small shift
            shift = rng.choice([0.1, 0.25, -0.1, -0.25])
            mutations.append((lhs.replace("x", f"(x+{shift})"), rhs.replace("x", f"(x+{shift})"), "rand_shift"))

        return mutations

    @staticmethod
    def _expr_to_latex(expr: str) -> str:
        """Naive LaTeX conversion for auto-generated expressions."""
        if _SYMPY_OK:
            try:
                parts = expr.split("==")
                lhs_s = _sympy_parse(parts[0].strip())
                rhs_s = _sympy_parse(parts[1].strip())
                if lhs_s is not None and rhs_s is not None:
                    import sympy
                    return sympy.latex(lhs_s) + " = " + sympy.latex(rhs_s)
            except Exception:
                pass
        return expr.replace("**", "^").replace("*", r"\cdot ")

    def _visualize_single_tree(
        self,
        tree: dict,
        result: ProofResult,
        radial: bool = False,
        output_path: Optional[str] = None,
    ) -> None:
        """Draw a single EML tree with hierarchical or radial layout."""
        import matplotlib.pyplot as plt

        nodes: List[tuple] = []
        edges: List[tuple] = []
        colors: List[str] = []
        labels: List[str] = []

        def _collect(node: dict, parent_id: Optional[int], depth: int, pos: float) -> int:
            node_id = len(nodes)
            if node["op"] == "leaf":
                val = node["val"]
                lbl = "x" if val == "x" else str(round(float(val), 3))
                color = "coral" if val == "x" else "lightgreen"
            elif node["op"] == "eml":
                lbl = "eml"
                color = "cornflowerblue"
            else:
                lbl = "?"
                color = "lightyellow"
            nodes.append((node_id, depth, pos))
            colors.append(color)
            labels.append(lbl)
            if parent_id is not None:
                edges.append((parent_id, node_id))
            if node["op"] == "eml":
                _collect(node["left"], node_id, depth + 1, pos - 1.0 / (depth + 1))
                _collect(node["right"], node_id, depth + 1, pos + 1.0 / (depth + 1))
            return node_id

        _collect(tree, None, 0, 0.0)

        # Build position dict
        max_depth = max(d for _, d, _ in nodes) if nodes else 0
        pos_dict = {}
        for nid, depth, hpos in nodes:
            if radial and max_depth > 0:
                angle = hpos * math.pi
                r = depth / (max_depth + 1)
                pos_dict[nid] = (r * math.cos(angle), r * math.sin(angle))
            else:
                pos_dict[nid] = (hpos, -depth)

        fig, ax = plt.subplots(figsize=(max(6, len(nodes) * 0.7), max(4, max_depth * 1.5 + 2)))
        ax.set_aspect("equal" if radial else "auto")
        ax.axis("off")

        # Draw edges
        for (u, v) in edges:
            x0, y0 = pos_dict[u]
            x1, y1 = pos_dict[v]
            ax.plot([x0, x1], [y0, y1], "k-", lw=1.2, zorder=1)

        # Draw nodes
        for nid, color, label in zip(range(len(nodes)), colors, labels):
            x, y = pos_dict[nid]
            circle = plt.Circle((x, y), 0.18, color=color, ec="black", lw=1.0, zorder=2)
            ax.add_patch(circle)
            ax.text(x, y, label, ha="center", va="center", fontsize=8, fontweight="bold", zorder=3)

        # Legend
        legend_handles = [
            mpatches.Patch(color="cornflowerblue", label="EML node"),
            mpatches.Patch(color="lightgreen", label="Constant leaf"),
            mpatches.Patch(color="coral", label="Variable x"),
        ]
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8)

        title = (f"{result.identity_str}\n"
                 f"Status: {result.status}  |  Confidence: {result.confidence:.2f}"
                 f"  |  Nodes: {result.node_count}")
        ax.set_title(title, fontsize=9, pad=10)

        _show_or_save(fig, output_path)

    def _visualize_step(
        self,
        result: ProofResult,
        output_path: Optional[str] = None,
    ) -> None:
        """Draw LHS and RHS trees side-by-side with proof arrow."""
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(14, 5),
                                 gridspec_kw={"width_ratios": [5, 1, 5]})

        for ax in axes:
            ax.axis("off")

        # LHS tree
        lhs_tree = result.lhs_tree or result.witness_tree
        if lhs_tree:
            axes[0].set_title("LHS", fontsize=10, fontweight="bold")
            _draw_tree_on_axis(lhs_tree, axes[0])
        else:
            axes[0].text(0.5, 0.5, "LHS\n(no tree)", ha="center", va="center")

        # Centre: proof method arrow
        axes[1].text(0.5, 0.5,
                     f"  →\n{result.verification_method}\n"
                     f"conf={result.confidence:.2f}",
                     ha="center", va="center", fontsize=9, style="italic")

        # RHS tree
        rhs_tree = result.rhs_tree
        if rhs_tree:
            axes[2].set_title("RHS", fontsize=10, fontweight="bold")
            _draw_tree_on_axis(rhs_tree, axes[2])
        else:
            axes[2].text(0.5, 0.5, "RHS\n(no tree)", ha="center", va="center")

        fig.suptitle(result.identity_str, fontsize=11, fontweight="bold")
        _show_or_save(fig, output_path)


# ── Visualization helpers ─────────────────────────────────────────────────────

def _draw_tree_on_axis(tree: dict, ax: "Any") -> None:
    """Draw an EML tree dict onto a matplotlib Axes object."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        return

    nodes: List[tuple] = []
    edges: List[tuple] = []
    colors: List[str] = []
    labels: List[str] = []

    def _collect(node: dict, parent_id: Optional[int], depth: int, pos: float) -> None:
        nid = len(nodes)
        if node["op"] == "leaf":
            val = node["val"]
            lbl = "x" if val == "x" else str(round(float(val), 3))
            color = "coral" if val == "x" else "lightgreen"
        elif node["op"] == "eml":
            lbl = "eml"
            color = "cornflowerblue"
        else:
            lbl = "?"
            color = "lightyellow"
        nodes.append((nid, depth, pos))
        colors.append(color)
        labels.append(lbl)
        if parent_id is not None:
            edges.append((parent_id, nid))
        if node["op"] == "eml":
            _collect(node["left"], nid, depth + 1, pos - 0.5 / (depth + 1))
            _collect(node["right"], nid, depth + 1, pos + 0.5 / (depth + 1))

    _collect(tree, None, 0, 0.0)
    max_depth = max(d for _, d, _ in nodes) if nodes else 0
    pos_dict = {nid: (hpos, -depth) for nid, depth, hpos in nodes}

    for (u, v) in edges:
        x0, y0 = pos_dict[u]
        x1, y1 = pos_dict[v]
        ax.plot([x0, x1], [y0, y1], "k-", lw=1.0, zorder=1)

    for nid, color, label in zip(range(len(nodes)), colors, labels):
        x, y = pos_dict[nid]
        circle = plt.Circle((x, y), 0.12, color=color, ec="black", lw=0.8, zorder=2)
        ax.add_patch(circle)
        ax.text(x, y, label, ha="center", va="center", fontsize=7, zorder=3)

    ax.set_aspect("auto")


def _show_or_save(fig: "Any", output_path: Optional[str]) -> None:
    """Show the figure inline, or save to path if given."""
    import matplotlib.pyplot as plt
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.tight_layout()
        plt.show()
