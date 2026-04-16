"""
monogate.sympy_bridge — SymPy interoperability for EML expressions.

Converts EML expression trees (as produced by monogate search functions)
to and from SymPy expressions.  Enables symbolic simplification, LaTeX
rendering, and identity verification.

SymPy is an optional dependency.  All functions raise ``ImportError`` with
install instructions if sympy is not available.

Install::

    pip install monogate[sympy]
    # or
    pip install sympy>=1.12

Public API
----------
to_sympy(tree, x_sym=None)     -> sympy.Expr
from_sympy(expr)               -> dict  (best-effort; exp/log only)
simplify_eml(tree)             -> sympy.Expr
latex_eml(tree)                -> str
verify_identity(tree1, tree2)  -> bool
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "to_sympy",
    "from_sympy",
    "simplify_eml",
    "latex_eml",
    "verify_identity",
]

_SYMPY_MISSING_MSG = (
    "sympy is required for monogate.sympy_bridge.\n"
    "Install it with:  pip install monogate[sympy]\n"
    "or:               pip install sympy>=1.12"
)


def _require_sympy():
    """Import and return sympy, raising ImportError with helpful message if absent."""
    try:
        import sympy
        return sympy
    except ImportError:
        raise ImportError(_SYMPY_MISSING_MSG) from None


# ── EML tree → SymPy ──────────────────────────────────────────────────────────


def to_sympy(
    tree: dict[str, Any] | str,
    x_sym=None,
):
    """Convert an EML expression tree to a SymPy expression.

    Recursively maps::

        leaf("x")          → x_sym  (default: sympy.Symbol("x"))
        leaf(c)            → sympy.Float(c)  or  sympy.Integer(c)
        eml(a, b)          → exp(a_sym) - log(b_sym)

    Args:
        tree:   EML tree dict (``{"op": "eml", "left": ..., "right": ...}``)
                or string leaf shorthand (``"x"``, ``"1"``).
        x_sym:  SymPy symbol to use for the input variable.  Defaults to
                ``sympy.Symbol("x")``.

    Returns:
        A SymPy expression.

    Raises:
        ImportError: If sympy is not installed.
        TypeError:   If tree has an unrecognised structure.

    Examples::

        >>> import sympy; x = sympy.Symbol("x")
        >>> to_sympy({"op": "eml", "left": {"op": "leaf", "val": "x"},
        ...                        "right": {"op": "leaf", "val": 1.0}}, x)
        exp(x) - log(1)
        >>> sympy.simplify(_)
        exp(x)
    """
    sp = _require_sympy()

    if x_sym is None:
        x_sym = sp.Symbol("x")

    # String shorthand
    if isinstance(tree, str):
        if tree == "x":
            return x_sym
        try:
            v = float(tree)
            return sp.Integer(int(v)) if float(v) == int(float(v)) else sp.Float(v)
        except ValueError:
            raise TypeError(f"to_sympy: unknown string leaf {tree!r}")

    if not isinstance(tree, dict):
        raise TypeError(f"to_sympy: expected dict or str, got {type(tree)!r}")

    op = tree.get("op")

    if op == "leaf":
        val = tree["val"]
        if val == "x":
            return x_sym
        if isinstance(val, (int, float)):
            v = float(val)
            return sp.Integer(int(v)) if v == int(v) else sp.Float(v)
        raise TypeError(f"to_sympy: unknown leaf val {val!r}")

    if op == "eml":
        a_expr = to_sympy(tree["left"], x_sym)
        b_expr = to_sympy(tree["right"], x_sym)
        return sp.exp(a_expr) - sp.log(b_expr)

    if op == "?":
        raise ValueError(
            "to_sympy: tree contains unexpanded placeholder '?'. "
            "Fully expand the tree before converting."
        )

    raise TypeError(f"to_sympy: unknown op {op!r}")


# ── SymPy → EML tree (best-effort) ───────────────────────────────────────────


def from_sympy(expr) -> dict[str, Any]:
    """Convert a SymPy expression to an EML tree (best-effort).

    Only handles expressions that are direct compositions of ``exp`` and
    ``log`` (and their differences).  More complex expressions raise
    ``NotImplementedError``.

    Args:
        expr: SymPy expression.

    Returns:
        EML tree dict.

    Raises:
        ImportError:        If sympy is not installed.
        NotImplementedError: If the expression cannot be converted to EML.

    Examples::

        >>> import sympy; x = sympy.Symbol("x")
        >>> from_sympy(sympy.exp(x))
        {"op": "eml", "left": {"op": "leaf", "val": "x"},
                       "right": {"op": "leaf", "val": 1.0}}
        # Because exp(x) = exp(x) - log(1) = eml(x, 1)
    """
    sp = _require_sympy()

    # exp(a)  →  eml(a, 1)
    if expr.func == sp.exp:
        inner = expr.args[0]
        return {
            "op": "eml",
            "left": from_sympy(inner),
            "right": {"op": "leaf", "val": 1.0},
        }

    # -log(b)  →  eml(0, b)
    if expr.func == sp.log:
        inner = expr.args[0]
        return {
            "op": "eml",
            "left": {"op": "leaf", "val": 0.0},
            "right": from_sympy(inner),
        }

    # exp(a) - log(b) = eml(a, b)
    if expr.func == sp.Add and len(expr.args) == 2:
        a_s, b_s = expr.args
        # detect exp(a) + (-1)*log(b)
        if a_s.func == sp.exp:
            try:
                neg_log = b_s
                if neg_log.func == sp.Mul:
                    coef, logterm = neg_log.args
                    if coef == -1 and logterm.func == sp.log:
                        return {
                            "op": "eml",
                            "left": from_sympy(a_s.args[0]),
                            "right": from_sympy(logterm.args[0]),
                        }
            except (AttributeError, ValueError):
                pass

    # Symbol "x"
    if expr.func == sp.Symbol and expr.name == "x":
        return {"op": "leaf", "val": "x"}

    # Integer or Float constant
    if expr.is_Number:
        v = float(expr)
        return {"op": "leaf", "val": v}

    raise NotImplementedError(
        f"from_sympy: cannot convert {expr!r} to EML tree. "
        "Only exp/log compositions are supported."
    )


# ── simplify_eml ──────────────────────────────────────────────────────────────


def simplify_eml(tree: dict[str, Any] | str):
    """Convert EML tree to SymPy and apply sympy.simplify().

    Args:
        tree: EML tree dict or string leaf.

    Returns:
        Simplified SymPy expression.

    Raises:
        ImportError: If sympy is not installed.
    """
    sp = _require_sympy()
    return sp.simplify(to_sympy(tree))


# ── latex_eml ─────────────────────────────────────────────────────────────────


def latex_eml(tree: dict[str, Any] | str) -> str:
    """Return the LaTeX representation of an EML tree via SymPy.

    First converts to SymPy, then calls ``sympy.latex()``.

    Args:
        tree: EML tree dict or string leaf.

    Returns:
        LaTeX string (no surrounding $…$ delimiters).

    Raises:
        ImportError: If sympy is not installed.

    Examples::

        >>> latex_eml({"op": "eml", "left": {"op": "leaf", "val": "x"},
        ...                         "right": {"op": "leaf", "val": 1.0}})
        'e^{x} - \\\\log{\\\\left(1 \\\\right)}'
    """
    sp = _require_sympy()
    expr = to_sympy(tree)
    return sp.latex(expr)


# ── verify_identity ───────────────────────────────────────────────────────────


def verify_identity(
    tree1: dict[str, Any] | str,
    tree2: dict[str, Any] | str,
) -> bool:
    """Return True if SymPy can prove the two EML trees are symbolically equal.

    Converts both trees to SymPy, subtracts, and checks if the result
    simplifies to zero.

    Args:
        tree1: First EML tree.
        tree2: Second EML tree.

    Returns:
        True if trees are symbolically equal; False otherwise.

    Raises:
        ImportError: If sympy is not installed.

    Note:
        SymPy's simplifier is not complete — it may return False even for
        equal expressions if the identity requires non-trivial manipulation.

    Examples::

        # eml(eml(x,1), 1) = exp(exp(x)) — trivially equal
        >>> t1 = {"op": "eml", "left": {"op": "eml",
        ...           "left": {"op":"leaf","val":"x"},
        ...           "right": {"op":"leaf","val":1.0}},
        ...       "right": {"op":"leaf","val":1.0}}
        >>> t2 = {"op": "eml", "left": {"op": "eml",
        ...           "left": {"op":"leaf","val":"x"},
        ...           "right": {"op":"leaf","val":1.0}},
        ...       "right": {"op":"leaf","val":1.0}}
        >>> verify_identity(t1, t2)
        True
    """
    sp = _require_sympy()
    expr1 = to_sympy(tree1)
    expr2 = to_sympy(tree2)
    diff = sp.simplify(expr1 - expr2)
    return diff == 0
