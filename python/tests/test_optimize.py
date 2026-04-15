"""
Tests for monogate.optimize — best_optimize() API, BestRewriter, decorator.

Covers:
  - Expression string detection and node counting
  - Python/PyTorch code snippet rewriting
  - OptimizeResult fields and __str__
  - Decorator stub (callable passthrough)
  - Edge cases: empty input, unknown ops, no-savings expressions
"""

import ast
import math

import pytest

from monogate import best_optimize, optimize, OptimizeResult, OpMatch
from monogate.optimize import BestRewriter, _ast_rewrite


# ── Helpers ───────────────────────────────────────────────────────────────────

def op_by_name(result: OptimizeResult, name: str) -> OpMatch | None:
    return next((m for m in result.ops if m.name == name), None)


# ── Expression string mode ────────────────────────────────────────────────────

class TestExpressionString:
    def test_returns_optimize_result(self):
        r = best_optimize("sin(x)")
        assert isinstance(r, OptimizeResult)

    def test_sin_node_count(self):
        r = best_optimize("sin(x)")
        m = op_by_name(r, "sin")
        assert m is not None
        assert m.count == 1
        assert m.best_nodes == 63    # EXL 8-term Taylor
        assert m.eml_nodes  == 245   # pure EML
        assert m.best_op    == "EXL"

    def test_cos_node_count(self):
        r = best_optimize("cos(x)")
        m = op_by_name(r, "cos")
        assert m is not None
        assert m.best_nodes == 63
        assert m.eml_nodes  == 245

    def test_exp_no_savings(self):
        r = best_optimize("exp(x)")
        m = op_by_name(r, "exp")
        assert m is not None
        assert m.best_nodes == m.eml_nodes  # both 1 — no improvement
        assert m.savings == 0

    def test_ln_savings(self):
        r = best_optimize("ln(x)")
        m = op_by_name(r, "ln")
        assert m is not None
        assert m.best_nodes == 1    # EXL
        assert m.eml_nodes  == 3    # pure EML
        assert m.savings    == 67

    def test_pow_operator_savings(self):
        r = best_optimize("x**3")
        m = op_by_name(r, "pow")
        assert m is not None
        assert m.best_nodes == 3
        assert m.eml_nodes  == 15
        assert m.savings    == 80

    def test_multiple_ops_totals(self):
        # sin(x) + cos(x): 63+63=126 BEST, 245+245=490 EML + add overhead
        r = best_optimize("sin(x) + cos(x)")
        assert r.total_best_nodes > 0
        assert r.total_eml_nodes  > r.total_best_nodes
        assert r.savings_pct > 0

    def test_savings_pct_reasonable(self):
        # sin(x)**2 heavy on trig — should see 70%+ savings
        r = best_optimize("sin(x)**2 + cos(x)*x**3 + exp(-x)")
        assert r.savings_pct >= 60

    def test_rewritten_contains_best(self):
        r = best_optimize("sin(x) + cos(x)")
        assert "BEST.sin" in r.rewritten_code
        assert "BEST.cos" in r.rewritten_code

    def test_pow_simple_rewritten(self):
        r = best_optimize("x**3")
        assert "BEST.pow(x, 3)" in r.rewritten_code

    def test_python_snippet_importline(self):
        r = best_optimize("sin(x)")
        assert "from monogate import BEST" in r.python_snippet
        assert "def f(x):" in r.python_snippet

    def test_python_snippet_node_comment(self):
        r = best_optimize("sin(x)")
        assert "63" in r.python_snippet   # BEST node count appears in comment


# ── Python code snippet mode ──────────────────────────────────────────────────

class TestPythonCodeSnippet:
    TORCH_CODE = (
        "import torch\n"
        "def model(x):\n"
        "    return torch.sin(x)**2 + torch.cos(x) * x**3\n"
    )
    NUMPY_CODE = (
        "import numpy as np\n"
        "y = np.sin(x) + np.cos(x) / np.power(x, 2)\n"
    )
    MATH_CODE = (
        "import math\n"
        "def f(x):\n"
        "    return math.exp(x) / math.log(x + 1)\n"
    )

    def test_detects_torch_sin(self):
        r = best_optimize(self.TORCH_CODE)
        m = op_by_name(r, "sin")
        assert m is not None and m.count >= 1

    def test_detects_torch_cos(self):
        r = best_optimize(self.TORCH_CODE)
        m = op_by_name(r, "cos")
        assert m is not None and m.count >= 1

    def test_rewrites_torch_sin(self):
        r = best_optimize(self.TORCH_CODE)
        assert "BEST.sin(" in r.rewritten_code
        assert "torch.sin" not in r.rewritten_code

    def test_rewrites_torch_cos(self):
        r = best_optimize(self.TORCH_CODE)
        assert "BEST.cos(" in r.rewritten_code

    def test_rewrites_np_sin(self):
        r = best_optimize(self.NUMPY_CODE)
        assert "BEST.sin(" in r.rewritten_code
        assert "np.sin" not in r.rewritten_code

    def test_rewrites_np_power(self):
        r = best_optimize(self.NUMPY_CODE)
        assert "BEST.pow(" in r.rewritten_code

    def test_rewrites_math_log(self):
        r = best_optimize(self.MATH_CODE)
        assert "BEST.ln(" in r.rewritten_code
        assert "math.log" not in r.rewritten_code

    def test_rewrites_math_exp(self):
        r = best_optimize(self.MATH_CODE)
        assert "BEST.exp(" in r.rewritten_code

    def test_rewritten_code_includes_best_import(self):
        r = best_optimize(self.TORCH_CODE)
        assert "from monogate import BEST" in r.python_snippet

    def test_savings_detected_on_code(self):
        r = best_optimize(self.TORCH_CODE)
        assert r.savings_pct > 0

    def test_div_rewritten(self):
        code = "import torch\ny = torch.div(a, b)"
        r = best_optimize(code)
        assert "BEST.div(" in r.rewritten_code

    def test_mul_rewritten(self):
        code = "import numpy as np\ny = np.multiply(a, b)"
        r = best_optimize(code)
        assert "BEST.mul(" in r.rewritten_code


# ── OptimizeResult structure ──────────────────────────────────────────────────

class TestOptimizeResult:
    def test_original_preserved(self):
        expr = "sin(x) + ln(x)"
        r = best_optimize(expr)
        assert r.original == expr

    def test_ops_are_immutable_tuple(self):
        r = best_optimize("sin(x)")
        assert isinstance(r.ops, tuple)

    def test_explanation_is_tuple_of_strings(self):
        r = best_optimize("sin(x)")
        assert isinstance(r.explanation, tuple)
        assert all(isinstance(e, str) for e in r.explanation)

    def test_str_contains_totals(self):
        r = best_optimize("sin(x)")
        s = str(r)
        assert "TOTAL" in s
        assert "sin" in s

    def test_message_contains_savings(self):
        r = best_optimize("sin(x)")
        assert "%" in r.message

    def test_op_match_savings_property(self):
        r = best_optimize("sin(x)")
        m = op_by_name(r, "sin")
        assert m.savings == round((1 - 63 / 245) * 100)


# ── Dict-style access on OptimizeResult ──────────────────────────────────────

class TestDictAccess:
    def test_message_dict_style(self):
        r = best_optimize("sin(x)")
        assert r["message"] == r.message

    def test_savings_pct_dict_style(self):
        r = best_optimize("sin(x)")
        assert r["savings_pct"] == r.savings_pct

    def test_python_snippet_dict_style(self):
        r = best_optimize("sin(x)")
        assert r["python_snippet"] == r.python_snippet

    def test_unknown_key_raises(self):
        r = best_optimize("sin(x)")
        with pytest.raises(KeyError):
            _ = r["nonexistent_field"]

    def test_keys_returns_sorted_list(self):
        r = best_optimize("sin(x)")
        assert isinstance(r.keys(), list)
        assert "message" in r.keys()
        assert "savings_pct" in r.keys()


# ── Decorator — AST analysis ──────────────────────────────────────────────────

class TestDecoratorAst:
    def test_callable_returned(self):
        def my_fn(x):
            import math
            return math.sin(x)

        result = best_optimize(my_fn)
        assert callable(result)

    def test_decorated_fn_still_callable(self):
        @best_optimize
        def my_fn(x):
            return x + 1

        assert my_fn(3) == 4

    def test_best_info_attached(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x) + math.cos(x)

        assert hasattr(my_fn, "best_info")
        assert isinstance(my_fn.best_info, OptimizeResult)

    def test_best_info_detects_sin(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x)

        m = op_by_name(my_fn.best_info, "sin")
        assert m is not None
        assert m.best_nodes == 63

    def test_best_info_savings_positive(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x) * math.cos(x)

        assert my_fn.best_info.savings_pct > 0

    def test_stub_marker_set(self):
        @best_optimize
        def my_fn(x):
            return x

        assert getattr(my_fn, "_best_optimize_stub", False) is True

    def test_bare_decorator_no_parens(self):
        # @best_optimize  (no parentheses)
        @best_optimize
        def f(x):
            import math
            return math.exp(x)

        assert callable(f)
        assert hasattr(f, "best_info")

    def test_with_parens_decorator(self):
        # @best_optimize()  (with empty parentheses)
        @best_optimize()
        def g(x):
            import math
            return math.sin(x)

        assert callable(g)
        assert hasattr(g, "best_info")

    def test_wraps_preserves_name(self):
        @best_optimize
        def my_named_fn(x):
            return x

        assert my_named_fn.__name__ == "my_named_fn"

    def test_optimize_alias(self):
        r = optimize("sin(x)")
        assert isinstance(r, OptimizeResult)


# ── BestRewriter AST transformer ─────────────────────────────────────────────

class TestBestRewriter:
    def _rewrite(self, src: str) -> str:
        tree = ast.parse(src, mode="eval")
        new_tree = BestRewriter().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def test_bare_sin_rewritten(self):
        assert self._rewrite("sin(x)") == "BEST.sin(x)"

    def test_bare_cos_rewritten(self):
        assert self._rewrite("cos(x)") == "BEST.cos(x)"

    def test_bare_exp_rewritten(self):
        assert self._rewrite("exp(x)") == "BEST.exp(x)"

    def test_bare_log_rewritten_to_ln(self):
        assert self._rewrite("log(x)") == "BEST.ln(x)"

    def test_bare_pow_rewritten(self):
        assert self._rewrite("pow(x, 3)") == "BEST.pow(x, 3)"

    def test_attr_math_sin_rewritten(self):
        assert self._rewrite("math.sin(x)") == "BEST.sin(x)"

    def test_attr_torch_cos_rewritten(self):
        assert self._rewrite("torch.cos(x)") == "BEST.cos(x)"

    def test_attr_np_log_rewritten(self):
        assert self._rewrite("np.log(x)") == "BEST.ln(x)"

    def test_pow_binop_rewritten(self):
        assert self._rewrite("x ** 3") == "BEST.pow(x, 3)"

    def test_mul_binop_rewritten(self):
        assert self._rewrite("x * y") == "BEST.mul(x, y)"

    def test_div_binop_rewritten(self):
        assert self._rewrite("x / y") == "BEST.div(x, y)"

    def test_add_binop_rewritten(self):
        assert self._rewrite("x + y") == "BEST.add(x, y)"

    def test_sub_binop_rewritten(self):
        assert self._rewrite("x - y") == "BEST.sub(x, y)"

    def test_nested_expression_rewritten(self):
        # sin(x)**2 → BEST.pow(BEST.sin(x), 2)
        result = self._rewrite("sin(x) ** 2")
        assert "BEST.pow" in result
        assert "BEST.sin" in result

    def test_complex_expression_rewritten(self):
        result = self._rewrite("math.sin(x) + math.cos(x) * x ** 3")
        assert "BEST.sin" in result
        assert "BEST.cos" in result
        assert "BEST.pow" in result
        assert "BEST.mul" in result
        assert "BEST.add" in result

    def test_ast_rewrite_helper(self):
        result = _ast_rewrite("def f(x):\n    return math.sin(x)")
        assert "BEST.sin" in result

    def test_ast_rewrite_invalid_syntax_fallback(self):
        bad = "def (!!!"
        result = _ast_rewrite(bad)
        assert result == bad  # original returned unchanged


# ── Decorator — rewritten source ─────────────────────────────────────────────

class TestDecoratorRewrittenSource:
    def test_rewritten_source_attached(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x) + math.cos(x)

        assert hasattr(my_fn, "_best_rewritten_source")
        assert isinstance(my_fn._best_rewritten_source, str)

    def test_rewritten_source_contains_best(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x) * math.cos(x)

        assert "BEST.sin" in my_fn._best_rewritten_source
        assert "BEST.cos" in my_fn._best_rewritten_source

    def test_original_source_attached(self):
        @best_optimize
        def my_fn(x):
            return x

        assert hasattr(my_fn, "_best_original_source")
        assert "my_fn" in my_fn._best_original_source

    def test_is_best_optimized_flag(self):
        @best_optimize
        def my_fn(x):
            return x

        assert my_fn._is_best_optimized is True

    def test_python_snippet_uses_ast_rewrite(self):
        @best_optimize
        def my_fn(x):
            import math
            return math.sin(x)

        snippet = my_fn.best_info.python_snippet
        assert "BEST.sin" in snippet
        assert "from monogate import BEST" in snippet


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty input"):
            best_optimize("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty input"):
            best_optimize("   ")

    def test_wrong_type_raises(self):
        with pytest.raises(TypeError, match="str or callable"):
            best_optimize(42)  # type: ignore[arg-type]

    def test_no_savings_expression(self):
        # exp is the same cost in all operators — no improvement possible
        r = best_optimize("exp(x)")
        assert r.savings_pct == 0

    def test_add_symbol_detected(self):
        # "a + b" (multi-char names) — add operator is counted
        r = best_optimize("aa + bb")
        m = op_by_name(r, "add")
        assert m is not None
        assert m.savings == 0  # EML is already optimal for add

    def test_exp_only_no_savings(self):
        r = best_optimize("exp(x)")
        assert r.savings_pct == 0

    def test_multiple_same_op(self):
        r = best_optimize("sin(x) + sin(y) + sin(z)")
        m = op_by_name(r, "sin")
        assert m is not None
        assert m.count == 3
        assert m.best_nodes == 3 * 63
        assert m.eml_nodes  == 3 * 245

    def test_pow_count_via_operator(self):
        r = best_optimize("x**2 + x**3")
        m = op_by_name(r, "pow")
        assert m is not None
        assert m.count >= 2
