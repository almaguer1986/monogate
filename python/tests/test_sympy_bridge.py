"""
Tests for monogate.sympy_bridge — SymPy interoperability for EML expressions.

All tests are skipped if sympy is not installed (optional dependency).

Covers:
- to_sympy: leaf x, leaf constant, eml nodes, nested trees
- to_sympy: exp(x) identity (eml(x,1) → exp(x) − log(1))
- to_sympy: custom x_sym
- to_sympy: raises TypeError for unknown op / unknown leaf
- from_sympy: exp(x) → eml(x, 1)
- from_sympy: symbol "x" → leaf x
- from_sympy: integer/float constant → leaf
- from_sympy: non-convertible raises NotImplementedError
- simplify_eml: eml(x,1) simplifies to exp(x)
- latex_eml: returns non-empty string
- verify_identity: identical trees → True, different → False
"""

from __future__ import annotations

import pytest

sympy = pytest.importorskip("sympy", reason="sympy not installed — skipping bridge tests")

from monogate.sympy_bridge import (
    from_sympy,
    latex_eml,
    simplify_eml,
    to_sympy,
    verify_identity,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

x_sym = sympy.Symbol("x")

def _leaf_x():
    return {"op": "leaf", "val": "x"}

def _leaf_c(v):
    return {"op": "leaf", "val": v}

def _eml(left, right):
    return {"op": "eml", "left": left, "right": right}

# eml(x, 1) = exp(x) - log(1)
_TREE_EXP_X = _eml(_leaf_x(), _leaf_c(1.0))

# eml(eml(x,1), 1) = exp(exp(x)) - log(1)
_TREE_EXP_EXP_X = _eml(_TREE_EXP_X, _leaf_c(1.0))


# ── to_sympy ──────────────────────────────────────────────────────────────────

class TestToSympy:
    def test_leaf_x(self):
        result = to_sympy(_leaf_x())
        assert result == x_sym

    def test_leaf_constant_one(self):
        result = to_sympy(_leaf_c(1.0))
        assert result == sympy.Integer(1)

    def test_leaf_constant_float(self):
        result = to_sympy(_leaf_c(2.5))
        assert abs(float(result) - 2.5) < 1e-12

    def test_eml_x_1_is_exp_minus_log(self):
        result = to_sympy(_TREE_EXP_X)
        # Should be exp(x) - log(1)
        simplified = sympy.simplify(result)
        assert simplified == sympy.exp(x_sym)

    def test_eml_nested(self):
        result = to_sympy(_TREE_EXP_EXP_X)
        simplified = sympy.simplify(result)
        assert simplified == sympy.exp(sympy.exp(x_sym))

    def test_custom_x_sym(self):
        t = sympy.Symbol("t")
        tree = _eml(_leaf_x(), _leaf_c(1.0))
        result = to_sympy(tree, x_sym=t)
        assert t in result.free_symbols

    def test_string_x_shorthand(self):
        result = to_sympy("x")
        assert result == x_sym

    def test_string_constant_shorthand(self):
        result = to_sympy("1")
        assert result == sympy.Integer(1)

    def test_unknown_op_raises(self):
        tree = {"op": "add", "left": _leaf_x(), "right": _leaf_c(1.0)}
        with pytest.raises(TypeError, match="unknown op"):
            to_sympy(tree)

    def test_placeholder_raises(self):
        tree = {"op": "?"}
        with pytest.raises(ValueError, match="unexpanded placeholder"):
            to_sympy(tree)

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            to_sympy(42)


# ── from_sympy ────────────────────────────────────────────────────────────────

class TestFromSympy:
    def test_symbol_x(self):
        result = from_sympy(x_sym)
        assert result["op"] == "leaf"
        assert result["val"] == "x"

    def test_integer_constant(self):
        result = from_sympy(sympy.Integer(1))
        assert result["op"] == "leaf"
        assert float(result["val"]) == pytest.approx(1.0)

    def test_float_constant(self):
        result = from_sympy(sympy.Float(3.14))
        assert result["op"] == "leaf"
        assert float(result["val"]) == pytest.approx(3.14, abs=1e-5)

    def test_exp_x(self):
        # exp(x) → eml(x, 1)
        result = from_sympy(sympy.exp(x_sym))
        assert result["op"] == "eml"
        assert result["left"]["val"] == "x"
        assert float(result["right"]["val"]) == pytest.approx(1.0)

    def test_non_convertible_raises(self):
        with pytest.raises(NotImplementedError):
            from_sympy(sympy.sin(x_sym))


# ── simplify_eml ──────────────────────────────────────────────────────────────

class TestSimplifyEml:
    def test_eml_x_1_simplifies_to_exp_x(self):
        result = simplify_eml(_TREE_EXP_X)
        assert result == sympy.exp(x_sym)

    def test_leaf_x(self):
        result = simplify_eml(_leaf_x())
        assert result == x_sym

    def test_returns_sympy_expr(self):
        result = simplify_eml(_TREE_EXP_X)
        assert isinstance(result, sympy.Basic)


# ── latex_eml ─────────────────────────────────────────────────────────────────

class TestLatexEml:
    def test_returns_string(self):
        result = latex_eml(_TREE_EXP_X)
        assert isinstance(result, str)

    def test_nonempty(self):
        result = latex_eml(_TREE_EXP_X)
        assert len(result) > 0

    def test_contains_exp(self):
        result = latex_eml(_TREE_EXP_X)
        # LaTeX for exp(x) should contain 'e^'
        assert "e^" in result or "exp" in result.lower()


# ── verify_identity ───────────────────────────────────────────────────────────

class TestVerifyIdentity:
    def test_identical_trees(self):
        assert verify_identity(_TREE_EXP_X, _TREE_EXP_X) is True

    def test_different_constants(self):
        t1 = _leaf_c(1.0)
        t2 = _leaf_c(2.0)
        assert verify_identity(t1, t2) is False

    def test_same_nested_structure(self):
        assert verify_identity(_TREE_EXP_EXP_X, _TREE_EXP_EXP_X) is True

    def test_returns_bool(self):
        result = verify_identity(_TREE_EXP_X, _TREE_EXP_X)
        assert isinstance(result, bool)
