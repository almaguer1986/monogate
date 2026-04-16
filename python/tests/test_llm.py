"""
tests/test_llm.py — Tests for monogate.llm (mock provider only).

All tests use provider='mock' — no API key required.
LLM API provider tests (openai/groq/anthropic) are skipped unless
the corresponding env var is set.
"""

from __future__ import annotations

import math
import os

import pytest

from monogate.llm import suggest_and_optimize, LLMOptimizeResult, SUPPORTED_PROVIDERS
from monogate.llm.prompts import mock_response
from monogate.llm.optimizer import _analyze_expression, _rewrite_to_best


# ── mock_response ─────────────────────────────────────────────────────────────

class TestMockResponse:
    def test_sigmoid_returns_exp_expression(self) -> None:
        expr = mock_response("sigmoid function")
        assert "exp" in expr

    def test_gelu_returns_expression(self) -> None:
        expr = mock_response("GELU activation")
        assert len(expr) > 5

    def test_unknown_falls_back(self) -> None:
        expr = mock_response("some completely unknown function xyz123")
        assert "exp" in expr  # fallback is math.exp(x)

    def test_softplus(self) -> None:
        expr = mock_response("softplus")
        assert "log" in expr or "exp" in expr

    @pytest.mark.parametrize("prompt", [
        "sigmoid", "gelu", "swish", "relu", "exp", "log",
        "gaussian", "tanh", "softplus", "mish",
    ])
    def test_all_keywords_return_nonempty(self, prompt: str) -> None:
        expr = mock_response(prompt)
        assert isinstance(expr, str) and len(expr) > 0


# ── _analyze_expression ────────────────────────────────────────────────────────

class TestAnalyzeExpression:
    def test_simple_exp(self) -> None:
        ops, eml, best, pct = _analyze_expression("math.exp(x)")
        assert "exp" in ops
        assert eml >= best >= 0

    def test_composite_sigmoid(self) -> None:
        expr = "math.exp(x) / (1.0 + math.exp(x))"
        ops, eml, best, pct = _analyze_expression(expr)
        assert "exp" in ops
        assert "div" in ops
        assert best <= eml

    def test_savings_bounded(self) -> None:
        ops, eml, best, pct = _analyze_expression("math.exp(x) * math.log(x)")
        assert 0 <= pct <= 100

    def test_sin_detected(self) -> None:
        ops, eml, best, pct = _analyze_expression("math.sin(x)**2")
        assert "sin" in ops


# ── _rewrite_to_best ──────────────────────────────────────────────────────────

class TestRewriteToBest:
    def test_exp_rewrite(self) -> None:
        out = _rewrite_to_best("math.exp(x)")
        assert "BEST.exp" in out

    def test_log_rewrite(self) -> None:
        out = _rewrite_to_best("math.log(x)")
        assert "BEST.log" in out

    def test_composite_rewrite(self) -> None:
        out = _rewrite_to_best("math.exp(x) / (1.0 + math.exp(x))")
        assert "BEST.exp" in out
        assert "/" in out

    def test_no_math_prefix_unchanged(self) -> None:
        # x / (1 + x) has no math.* calls — should pass through unchanged
        out = _rewrite_to_best("x / (1.0 + x)")
        assert out == "x / (1.0 + x)"


# ── suggest_and_optimize (mock) ───────────────────────────────────────────────

class TestSuggestAndOptimize:
    def test_returns_result(self) -> None:
        r = suggest_and_optimize("sigmoid function")
        assert isinstance(r, LLMOptimizeResult)

    def test_fields_populated(self) -> None:
        r = suggest_and_optimize("exp function")
        assert r.prompt == "exp function"
        assert isinstance(r.llm_expression, str) and len(r.llm_expression) > 0
        assert isinstance(r.best_formula, str)
        assert r.eml_nodes >= 0
        assert r.best_nodes >= 0
        assert 0 <= r.savings_pct <= 100
        assert isinstance(r.code, str)
        assert r.provider == "mock"
        assert r.elapsed_s >= 0

    def test_provider_mock(self) -> None:
        r = suggest_and_optimize("log function", provider="mock")
        assert r.provider == "mock"

    def test_prompt_none_with_target_func(self) -> None:
        r = suggest_and_optimize(target_func=math.exp)
        assert isinstance(r, LLMOptimizeResult)
        assert "exp" in r.prompt.lower()

    def test_both_none_raises(self) -> None:
        with pytest.raises(ValueError, match="prompt"):
            suggest_and_optimize()

    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="provider"):
            suggest_and_optimize("test", provider="fakeprovider")

    def test_code_is_executable(self) -> None:
        r = suggest_and_optimize("exponential function")
        # code should be a valid lambda definition
        assert r.code.startswith("f = lambda x:")

    @pytest.mark.parametrize("prompt", [
        "sigmoid", "GELU", "softplus", "tanh", "exp(-x^2)",
    ])
    def test_various_prompts(self, prompt: str) -> None:
        r = suggest_and_optimize(prompt)
        assert r.best_nodes >= 0
        assert r.eml_nodes >= r.best_nodes

    def test_run_mcts_adds_fields(self) -> None:
        r = suggest_and_optimize(
            "exp function",
            target_func=math.exp,
            run_mcts=True,
            mcts_sims=200,  # fast for testing
        )
        # mcts_formula should be non-empty when mcts is available
        assert isinstance(r.mcts_formula, str)
        assert isinstance(r.mcts_mse, float)

    def test_print_summary_no_crash(self, capsys: pytest.CaptureFixture) -> None:
        r = suggest_and_optimize("sigmoid function")
        r.print_summary()
        captured = capsys.readouterr()
        assert "monogate" in captured.out.lower() or "sigmoid" in captured.out.lower()

    def test_repr(self) -> None:
        r = suggest_and_optimize("exp")
        s = repr(r)
        assert "LLMOptimizeResult" in s
        assert "provider" in s


# ── SUPPORTED_PROVIDERS ───────────────────────────────────────────────────────

class TestSupportedProviders:
    def test_contains_expected(self) -> None:
        for p in ("mock", "openai", "groq", "anthropic"):
            assert p in SUPPORTED_PROVIDERS


# ── CLI ───────────────────────────────────────────────────────────────────────

class TestCLI:
    def test_basic_run(self, capsys: pytest.CaptureFixture) -> None:
        from monogate.llm.cli import main
        rc = main(["sigmoid function"])
        assert rc == 0
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_list_providers(self, capsys: pytest.CaptureFixture) -> None:
        from monogate.llm.cli import main
        rc = main(["--list-providers"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "mock" in out
        assert "openai" in out

    def test_no_prompt_returns_nonzero(self, capsys: pytest.CaptureFixture) -> None:
        from monogate.llm.cli import main
        rc = main([])
        assert rc == 1

    def test_unknown_provider_exits(self) -> None:
        from monogate.llm.cli import main
        # argparse raises SystemExit(2) for invalid choices
        with pytest.raises(SystemExit) as exc_info:
            main(["--provider", "fakeprovider", "test"])
        assert exc_info.value.code != 0


# ── Integration: openai (skip if no key) ─────────────────────────────────────

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
class TestOpenAIIntegration:
    def test_openai_call(self) -> None:
        r = suggest_and_optimize("sigmoid function", provider="openai")
        assert r.provider == "openai"
        assert "exp" in r.llm_expression.lower() or "/" in r.llm_expression


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set",
)
class TestGroqIntegration:
    def test_groq_call(self) -> None:
        r = suggest_and_optimize("GELU activation", provider="groq")
        assert r.provider == "groq"
        assert isinstance(r.llm_expression, str)
