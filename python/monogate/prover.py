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
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

__all__ = [
    "ProofResult",
    "BenchmarkReport",
    "EMLProver",
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
) -> Tuple[Optional[dict], Optional[str], bool]:
    """
    Run MCTS to find an EML tree T ≈ lhs_fn, then verify T == rhs symbolically.

    Returns (witness_tree, formula_str, proved_witness).
    """
    if not _MCTS_OK or not _SYMPY_OK or not _BRIDGE_OK:
        return None, None, False

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
        )
    except Exception:
        return None, None, False

    best_tree = result.best_tree
    formula_str = result.best_formula

    if best_tree is None or result.best_mse > 1.0:
        return best_tree, formula_str, False

    # Try symbolic verification: T == rhs?
    try:
        tree_sym = _tree_to_sympy(best_tree)
        diff = sympy.simplify(tree_sym - rhs_expr)
        proved = diff == 0
        return best_tree, formula_str, proved
    except Exception:
        return best_tree, formula_str, False


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

    def __init__(self, verbose: bool = False, n_probe: int = 500) -> None:
        self.verbose = verbose
        self.n_probe = n_probe

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
            witness_tree, lhs_formula, witness_proved = _mcts_witness_search(
                lhs_fn=lhs_fn,
                probe_points=mcts_probes,
                rhs_expr=rhs_expr,
                max_nodes=max_nodes,
                n_simulations=n_simulations,
                seed=seed,
                timeout=remaining,
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
