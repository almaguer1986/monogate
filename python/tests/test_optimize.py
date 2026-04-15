"""
Tests for monogate.optimize — best_optimize() API.

Covers:
  - Expression string detection and node counting
  - Python/PyTorch code snippet rewriting
  - OptimizeResult fields and __str__
  - Decorator stub (callable passthrough)
  - Edge cases: empty input, unknown ops, no-savings expressions
"""

import pytest

from monogate import best_optimize, optimize, OptimizeResult, OpMatch


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


# ── Callable passthrough (decorator stub) ────────────────────────────────────

class TestDecoratorStub:
    def test_callable_returned_unchanged(self):
        def my_fn(x):
            return x * 2

        result = best_optimize(my_fn)
        assert result is my_fn

    def test_decorated_fn_still_callable(self):
        @best_optimize
        def my_fn(x):
            return x + 1

        assert my_fn(3) == 4

    def test_stub_marker_set(self):
        def my_fn(x):
            return x

        result = best_optimize(my_fn)
        assert getattr(result, "_best_optimize_stub", False) is True

    def test_optimize_alias(self):
        r = optimize("sin(x)")
        assert isinstance(r, OptimizeResult)


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
