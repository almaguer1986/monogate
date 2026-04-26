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

    def test_sin_pow_rewritten_via_ast(self):
        # AST rewriting: sin(x)**2 → BEST.pow(BEST.sin(x), 2), not BEST.sin(x)**2
        r = best_optimize("sin(x)**2")
        assert "BEST.pow" in r.rewritten_code
        assert "BEST.sin" in r.rewritten_code
        assert "**" not in r.rewritten_code

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

    def test_best_compiled_attribute_present(self):
        @best_optimize
        def my_fn(x):
            return x

        # _best_compiled is False for functions with no EML ops (no speedup possible)
        assert hasattr(my_fn, "_best_compiled")
        assert my_fn._best_compiled is False

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

    # Expression strings (not valid module-level code on their own)
    def test_ast_rewrite_bare_expression_sin_pow(self):
        # sin(x)**2 should produce BEST.pow(BEST.sin(x), 2) — not BEST.sin(x)**2
        result = _ast_rewrite("sin(x)**2")
        assert "BEST.pow" in result
        assert "BEST.sin" in result
        # The **2 exponent should be inside BEST.pow, not a trailing **
        assert "**" not in result

    def test_ast_rewrite_bare_expression_complex(self):
        result = _ast_rewrite("sin(x)**2 + cos(x)*x**3 + exp(-x)")
        assert "BEST.pow" in result
        assert "BEST.sin" in result
        assert "BEST.cos" in result
        assert "BEST.exp" in result
        # No raw ** should remain (all powered via BEST.pow)
        assert "**" not in result

    def test_ast_rewrite_expr_string_module_code(self):
        # Module-level function def still works
        result = _ast_rewrite("def f(x):\n    return math.sin(x)")
        assert "BEST.sin" in result

    def test_ast_rewrite_expression_no_double_sentinel(self):
        # Sentinel prefix must be stripped from output
        result = _ast_rewrite("sin(x)")
        assert "_best_expr_" not in result


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


# ── New ops: sigmoid / tanh / gelu ────────────────────────────────────────────

class TestCompoundOps:
    def test_sigmoid_detected_torch(self):
        r = best_optimize("import torch\ny = torch.sigmoid(x)")
        m = op_by_name(r, "sigmoid")
        assert m is not None
        assert m.best_nodes == 19
        assert m.eml_nodes  == 36
        assert m.savings    == 47

    def test_tanh_detected_torch(self):
        r = best_optimize("import torch\ny = torch.tanh(x)")
        m = op_by_name(r, "tanh")
        assert m is not None
        assert m.best_nodes == 25
        assert m.eml_nodes  == 45
        assert m.savings    == 44

    def test_gelu_detected_F(self):
        r = best_optimize("import torch.nn.functional as F\ny = F.gelu(x)")
        m = op_by_name(r, "gelu")
        assert m is not None
        assert m.best_nodes == 60
        assert m.eml_nodes  == 115

    def test_tanh_rewritten_by_ast(self):
        rewritten = best_optimize("torch.tanh(x)").rewritten_code
        assert "BEST.tanh" in rewritten

    def test_sigmoid_rewritten_by_ast(self):
        rewritten = best_optimize("import torch\ntorch.sigmoid(x)").rewritten_code
        assert "BEST.sigmoid" in rewritten


# ── BenchmarkResult and benchmark_optimize ────────────────────────────────────

class TestBenchmarkResult:
    def test_returns_benchmark_result(self):
        from monogate import benchmark_optimize, sin_eml_taylor, sin_best_taylor
        from monogate import BenchmarkResult

        r = benchmark_optimize(sin_eml_taylor, sin_best_taylor, 1.5,
                               label="test_sin", node_savings_pct=74,
                               min_run_time=0.1)
        assert isinstance(r, BenchmarkResult)

    def test_speedup_positive(self):
        from monogate import benchmark_optimize, sin_eml_taylor, sin_best_taylor

        r = benchmark_optimize(sin_eml_taylor, sin_best_taylor, 1.5,
                               min_run_time=0.1)
        assert r.speedup > 1.0   # BEST is faster

    def test_before_us_greater_than_after(self):
        from monogate import benchmark_optimize, sin_eml_taylor, sin_best_taylor

        r = benchmark_optimize(sin_eml_taylor, sin_best_taylor, 1.5,
                               min_run_time=0.1)
        assert r.before_us > r.after_us

    def test_node_savings_preserved(self):
        from monogate import benchmark_optimize, sin_eml_taylor, sin_best_taylor

        r = benchmark_optimize(sin_eml_taylor, sin_best_taylor, 1.5,
                               node_savings_pct=74, min_run_time=0.1)
        assert r.node_savings_pct == 74

    def test_str_output(self):
        from monogate import BenchmarkResult

        r = BenchmarkResult(
            label="test", before_us=36.0, after_us=12.0,
            speedup=3.0, node_savings_pct=74,
        )
        s = str(r)
        assert "test" in s
        assert "36.0" in s
        assert "12.0" in s
        assert "3.00x" in s
        assert "74%" in s

    def test_sin_reference_implementations_agree(self):
        """sin_eml_taylor and sin_best_taylor must return same value."""
        import math
        from monogate import sin_eml_taylor, sin_best_taylor

        for x in [1.1, 1.5, 2.0, 2.5, 3.0]:
            eml  = sin_eml_taylor(x)
            best = sin_best_taylor(x)
            ref  = math.sin(x)
            assert abs(eml  - ref) < 1e-5, f"sin_eml_taylor({x}) off: {eml}"
            assert abs(best - ref) < 1e-5, f"sin_best_taylor({x}) off: {best}"

    def test_sin_eml_requires_x_gt_1(self):
        from monogate import sin_eml_taylor
        import pytest as _pytest

        with _pytest.raises(ValueError, match="x > 1"):
            sin_eml_taylor(0.5)


# ── Decorator: actual BEST compilation for EML-arithmetic code ────────────────

class TestDecoratorBestCompiled:
    def test_eml_function_compiled(self):
        """Decorator compiles EML-arithmetic functions to BEST-routed versions."""
        from monogate import sin_eml_taylor

        @best_optimize
        def f(x):
            return sin_eml_taylor(x)

        assert f._best_compiled is True

    def test_standard_math_not_compiled(self):
        """Decorator does NOT compile functions using native math.* (already fast)."""
        import math

        @best_optimize
        def f(x):
            return math.sin(x)

        assert f._best_compiled is False

    def test_compiled_result_matches_original(self):
        """BEST-compiled function must return same value as the EML version."""
        import math
        from monogate import sin_eml_taylor, sin_best_taylor

        @best_optimize
        def f(x):
            return sin_eml_taylor(x)

        assert f._best_compiled is True
        for x in [1.2, 1.5, 2.0, 2.5]:
            assert abs(f(x) - math.sin(x)) < 1e-5, f"f({x}) = {f(x)}, expected ≈ {math.sin(x)}"

    def test_compiled_is_faster(self):
        """BEST-compiled version must be faster than plain EML on a batch."""
        import timeit
        from monogate import sin_eml_taylor

        @best_optimize
        def fast_sin(x):
            return sin_eml_taylor(x)

        assert fast_sin._best_compiled is True

        runs = 500
        t_eml  = timeit.timeit(lambda: sin_eml_taylor(1.5), number=runs)
        t_best = timeit.timeit(lambda: fast_sin(1.5),        number=runs)
        # BEST should be at least 20% faster (typically 3x)
        assert t_best < t_eml * 0.9, (
            f"Expected BEST ({t_best*1e6/runs:.1f} us) < EML ({t_eml*1e6/runs:.1f} us)"
        )

    def test_decorated_function_preserves_name(self):
        from monogate import sin_eml_taylor

        @best_optimize
        def my_eml_fn(x):
            return sin_eml_taylor(x)

        assert my_eml_fn.__name__ == "my_eml_fn"


# ── cos_best_taylor ───────────────────────────────────────────────────────────

class TestCosBestTaylor:
    def test_cos_zero(self):
        from monogate import cos_best_taylor
        assert cos_best_taylor(0.0) == 1.0

    def test_cos_accuracy(self):
        import math
        from monogate import cos_best_taylor
        for x in [0.5, 1.0, 1.5, 2.0, 3.0]:
            assert abs(cos_best_taylor(x) - math.cos(x)) < 1e-5, (
                f"cos_best_taylor({x}) = {cos_best_taylor(x)}, expected {math.cos(x)}"
            )

    def test_cos_negative_x(self):
        import math
        from monogate import cos_best_taylor
        assert abs(cos_best_taylor(-1.0) - math.cos(-1.0)) < 1e-5


# ── gelu_eml_approx / gelu_best_approx ───────────────────────────────────────

class TestGELUApprox:
    def _ref_gelu(self, x: float) -> float:
        import math
        return x * 0.5 * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))

    def test_gelu_eml_matches_ref(self):
        from monogate import gelu_eml_approx
        for x in [-2.0, -1.0, 0.0, 0.5, 1.0, 2.0]:
            approx = gelu_eml_approx(x)
            ref    = self._ref_gelu(x)
            assert abs(approx - ref) < 0.002, f"gelu_eml({x}): got {approx}, ref {ref}"

    def test_gelu_best_matches_ref(self):
        from monogate import gelu_best_approx
        for x in [-2.0, -1.0, 0.0, 0.5, 1.0, 2.0]:
            approx = gelu_best_approx(x)
            ref    = self._ref_gelu(x)
            assert abs(approx - ref) < 0.002, f"gelu_best({x}): got {approx}, ref {ref}"

    def test_gelu_eml_vs_best_agree(self):
        from monogate import gelu_eml_approx, gelu_best_approx
        for x in [-1.5, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]:
            assert abs(gelu_eml_approx(x) - gelu_best_approx(x)) < 1e-8, (
                f"EML and BEST GELU diverge at x={x}"
            )

    def test_gelu_best_not_dramatically_slower(self):
        # gelu_best uses EDL recip (2n) vs EML recip (5n) — the node-count
        # saving is real but micro-benchmarks at this scale are dominated by
        # Python function-call and complex-return overhead (BEST routes
        # recip through cmath-backed EDL, which has higher per-call overhead
        # than EML's math-backed recip even at fewer nodes). Bound is
        # deliberately loose to absorb noisy CI runners — we're guarding
        # against an order-of-magnitude regression, not micro-jitter.
        import timeit
        from monogate import gelu_eml_approx, gelu_best_approx
        runs = 2000
        t_eml  = timeit.timeit(lambda: gelu_eml_approx(1.0),  number=runs)
        t_best = timeit.timeit(lambda: gelu_best_approx(1.0), number=runs)
        assert t_best < t_eml * 5.0, (
            f"gelu_best ({t_best*1e6/runs:.1f} us) unexpectedly slow vs gelu_eml ({t_eml*1e6/runs:.1f} us)"
        )


# ── best_optimize_model ───────────────────────────────────────────────────────

class TestBestOptimizeModel:
    def test_requires_torch(self):
        from monogate import best_optimize_model
        # Just confirm it exists and is callable
        assert callable(best_optimize_model)

    def test_returns_model_optimize_report(self):
        pytest.importorskip("torch")
        import torch.nn as nn
        from monogate import best_optimize_model, ModelOptimizeReport

        model = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 1))
        report = best_optimize_model(model)
        assert isinstance(report, ModelOptimizeReport)

    def test_report_has_layers(self):
        pytest.importorskip("torch")
        import torch.nn as nn
        from monogate import best_optimize_model

        model = nn.Sequential(nn.Linear(4, 8), nn.Linear(8, 1))
        report = best_optimize_model(model)
        assert len(report.layers) > 0

    def test_report_str(self):
        pytest.importorskip("torch")
        import torch.nn as nn
        from monogate import best_optimize_model

        model = nn.Linear(4, 1)
        report = best_optimize_model(model)
        s = str(report)
        assert "ModelOptimizeReport" in s

    def test_layer_optimize_result_fields(self):
        pytest.importorskip("torch")
        import torch.nn as nn
        from monogate import best_optimize_model, LayerOptimizeResult

        model = nn.Linear(4, 1)
        report = best_optimize_model(model)
        for lr in report.layers:
            assert isinstance(lr, LayerOptimizeResult)
            assert isinstance(lr.path, str)
            assert lr.method == "forward"
            assert isinstance(lr.patched, bool)
