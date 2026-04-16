"""
tests/test_compile.py — Tests for monogate.compile.

Covers:
    FusedEMLActivation:  shape preservation, gradient flow, operator variants,
                         depth validation, element-wise invariance
    FusedEMLLayer:       shape, gradient, state_dict round-trip, n_eml_nodes
    compile_eml_layer:   returns a callable module, output matches original
    to_torchscript:      exports and runs correctly
    benchmark_layer:     returns BenchmarkTable with correct structure
"""

from __future__ import annotations

import io

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from monogate.compile import (
    FusedEMLActivation,
    FusedEMLLayer,
    BenchmarkTable,
    benchmark_layer,
    compile_eml_layer,
    to_torchscript,
)
from monogate.torch import EMLLayer


# ── Helpers ───────────────────────────────────────────────────────────────────

def _grad_ok(module: nn.Module, x: Tensor) -> bool:
    x = x.detach().requires_grad_(True)
    out = module(x)
    out.sum().backward()
    return all(
        p.grad is not None and torch.isfinite(p.grad).all()
        for p in module.parameters()
    )


# ── FusedEMLActivation ────────────────────────────────────────────────────────

class TestFusedEMLActivation:
    @pytest.mark.parametrize("depth", [1, 2, 3])
    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_shape_preserved(self, depth: int, operator: str) -> None:
        act = FusedEMLActivation(depth=depth, operator=operator)
        for shape in [(5,), (4, 8), (2, 3, 16)]:
            out = act(torch.randn(*shape))
            assert out.shape == torch.Size(shape)

    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_element_wise(self, operator: str) -> None:
        """Each output element depends only on the corresponding input scalar."""
        act    = FusedEMLActivation(depth=2, operator=operator)
        x      = torch.randn(3, 7)
        out    = act(x)
        scalar = x[1, 4].reshape(1)
        out_s  = act(scalar).item()
        assert abs(out[1, 4].item() - out_s) < 1e-5

    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_gradient_flow(self, operator: str) -> None:
        act = FusedEMLActivation(depth=2, operator=operator)
        assert _grad_ok(act, torch.randn(8, 16))

    def test_depth_0_raises(self) -> None:
        with pytest.raises(ValueError, match="depth"):
            FusedEMLActivation(depth=0)

    def test_depth_4_raises(self) -> None:
        with pytest.raises(ValueError, match="depth"):
            FusedEMLActivation(depth=4)

    def test_unknown_operator_raises(self) -> None:
        with pytest.raises(ValueError):
            FusedEMLActivation(operator="EDL")

    def test_parameters_exist(self) -> None:
        act = FusedEMLActivation(depth=2)
        params = list(act.parameters())
        assert len(params) == 2  # leaf_w and leaf_b

    def test_leaf_count(self) -> None:
        for d in [1, 2, 3]:
            act = FusedEMLActivation(depth=d)
            assert act.leaf_w.shape == (1 << d,)
            assert act.leaf_b.shape == (1 << d,)

    def test_output_finite(self) -> None:
        """Output should be finite for typical inputs (no overflow at depth 1-3)."""
        for depth in [1, 2, 3]:
            act = FusedEMLActivation(depth=depth)
            x   = torch.randn(64, 64)
            out = act(x)
            assert torch.isfinite(out).all(), f"Non-finite output at depth={depth}"


# ── FusedEMLLayer ─────────────────────────────────────────────────────────────

IN, OUT, BATCH = 8, 12, 16


class TestFusedEMLLayer:
    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_output_shape(self, operator: str) -> None:
        layer = FusedEMLLayer(IN, OUT, depth=2, operator=operator)
        out   = layer(torch.randn(BATCH, IN))
        assert out.shape == (BATCH, OUT)

    @pytest.mark.parametrize("depth", [1, 2, 3])
    def test_depth_variants(self, depth: int) -> None:
        layer = FusedEMLLayer(IN, OUT, depth=depth)
        out   = layer(torch.randn(BATCH, IN))
        assert out.shape == (BATCH, OUT)

    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_gradient_flow(self, operator: str) -> None:
        layer = FusedEMLLayer(IN, OUT, depth=2, operator=operator)
        assert _grad_ok(layer, torch.randn(BATCH, IN))

    def test_n_eml_nodes(self) -> None:
        for d in [1, 2, 3]:
            layer = FusedEMLLayer(IN, OUT, depth=d)
            assert layer.n_eml_nodes == (1 << d) - 1

    def test_n_parameters(self) -> None:
        layer = FusedEMLLayer(IN, OUT)
        assert layer.n_parameters == sum(p.numel() for p in layer.parameters())

    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_state_dict_round_trip(self, operator: str) -> None:
        torch.manual_seed(0)
        layer = FusedEMLLayer(IN, OUT, depth=2, operator=operator)
        x     = torch.randn(BATCH, IN)
        with torch.no_grad():
            before = layer(x).clone()

        buf = io.BytesIO()
        torch.save(layer.state_dict(), buf)
        buf.seek(0)
        layer2 = FusedEMLLayer(IN, OUT, depth=2, operator=operator)
        layer2.load_state_dict(torch.load(buf, weights_only=True))
        with torch.no_grad():
            after = layer2(x)

        assert torch.allclose(before, after, atol=1e-6)

    def test_training_reduces_loss(self) -> None:
        torch.manual_seed(42)
        layer = FusedEMLLayer(1, 1, depth=2)
        opt   = torch.optim.Adam(layer.parameters(), lr=1e-3)
        x     = torch.linspace(-1, 1, 50).unsqueeze(1)
        y     = x * x

        init_loss = F.mse_loss(layer(x).squeeze(), y.squeeze()).item()
        for _ in range(200):
            opt.zero_grad()
            loss = F.mse_loss(layer(x).squeeze(), y.squeeze())
            if not torch.isfinite(loss):
                break
            loss.backward()
            opt.step()
        final_loss = F.mse_loss(layer(x).squeeze(), y.squeeze()).item()
        assert final_loss < init_loss


# ── Fixture: detect if torch.compile actually works end-to-end ───────────────

def _torch_compile_works() -> bool:
    """Return True if torch.compile can compile and execute a trivial module."""
    if not hasattr(torch, "compile"):
        return False
    try:
        import warnings
        m = nn.Linear(2, 2)
        c = torch.compile(m)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with torch.no_grad():
                _ = c(torch.randn(1, 2))
        return True
    except Exception:
        return False


_COMPILE_WORKS = _torch_compile_works()
skip_no_compile = pytest.mark.skipif(
    not _COMPILE_WORKS,
    reason="torch.compile not functional on this platform (Python 3.14 / Windows)",
)


# ── compile_eml_layer ─────────────────────────────────────────────────────────

class TestCompileEMLLayer:
    def test_returns_callable(self) -> None:
        """compile_eml_layer always returns a callable (may fall back to original)."""
        layer    = EMLLayer(IN, OUT, depth=2)
        compiled = compile_eml_layer(layer)
        assert callable(compiled)

    @skip_no_compile
    def test_output_matches_original(self) -> None:
        """Compiled layer produces same results as original (after warm-up)."""
        import warnings
        torch.manual_seed(0)
        layer    = EMLLayer(IN, OUT, depth=2)
        x        = torch.randn(BATCH, IN)

        with torch.no_grad():
            expected = layer(x).clone()

        compiled = compile_eml_layer(layer)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with torch.no_grad():
                for _ in range(3):
                    compiled(x)
                out = compiled(x)

        assert out.shape == expected.shape
        assert torch.allclose(out, expected, atol=1e-4)

    @skip_no_compile
    def test_fused_layer_compiles(self) -> None:
        import warnings
        layer    = FusedEMLLayer(IN, OUT, depth=2)
        compiled = compile_eml_layer(layer)
        x        = torch.randn(BATCH, IN)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with torch.no_grad():
                out = compiled(x)
        assert out.shape == (BATCH, OUT)


# ── to_torchscript ────────────────────────────────────────────────────────────

class TestTorchScript:
    def test_fused_layer_trace(self) -> None:
        layer  = FusedEMLLayer(IN, OUT, depth=2)
        script = to_torchscript(layer, method="trace")
        x      = torch.randn(4, IN)
        with torch.no_grad():
            original = layer(x)
            scripted = script(x)
        assert torch.allclose(original, scripted, atol=1e-5)

    def test_eml_layer_trace(self) -> None:
        layer  = EMLLayer(IN, OUT, depth=2)
        script = to_torchscript(layer)
        x      = torch.randn(4, IN)
        with torch.no_grad():
            original = layer(x)
            scripted = script(x)
        assert torch.allclose(original, scripted, atol=1e-5)

    def test_save_load(self, tmp_path) -> None:
        layer  = FusedEMLLayer(IN, OUT, depth=2)
        script = to_torchscript(layer)
        path   = tmp_path / "fused.pt"
        torch.jit.save(script, str(path))
        loaded = torch.jit.load(str(path))
        x = torch.randn(4, IN)
        with torch.no_grad():
            a = script(x)
            b = loaded(x)
        assert torch.allclose(a, b, atol=1e-5)


# ── benchmark_layer ───────────────────────────────────────────────────────────

class TestBenchmarkLayer:
    def test_returns_table(self) -> None:
        layer  = FusedEMLLayer(IN, OUT, depth=2)
        table  = benchmark_layer(layer, batch_sizes=(4, 16), n_warmup=2, n_repeat=5)
        assert isinstance(table, BenchmarkTable)
        assert len(table.rows) == 2   # 1 layer × 2 batch sizes

    def test_two_layers(self) -> None:
        l1    = EMLLayer(IN, OUT, depth=2)
        l2    = FusedEMLLayer(IN, OUT, depth=2)
        table = benchmark_layer(l1, l2, batch_sizes=(8,), n_warmup=2, n_repeat=5)
        assert len(table.rows) == 2   # 2 layers × 1 batch size

    def test_baseline_speedup_is_one(self) -> None:
        layer = FusedEMLLayer(IN, OUT)
        table = benchmark_layer(layer, batch_sizes=(4,), n_warmup=1, n_repeat=3)
        # The first row should be the baseline
        assert table.rows[0].speedup == pytest.approx(1.0, abs=0.1)

    def test_print_table_no_crash(self, capsys) -> None:
        layer = FusedEMLLayer(IN, OUT)
        table = benchmark_layer(layer, batch_sizes=(4,), n_warmup=1, n_repeat=3)
        table.print_table()
        captured = capsys.readouterr()
        assert "benchmark" in captured.out.lower()

    def test_as_dict(self) -> None:
        layer = FusedEMLLayer(IN, OUT)
        table = benchmark_layer(layer, batch_sizes=(4,), n_warmup=1, n_repeat=3)
        d = table.as_dict()
        assert "rows" in d
        assert "in_features" in d

    def test_no_layers_raises(self) -> None:
        with pytest.raises(ValueError, match="least one"):
            benchmark_layer(batch_sizes=(4,))

    def test_custom_names(self) -> None:
        l1    = FusedEMLLayer(IN, OUT)
        l2    = FusedEMLLayer(IN, OUT)
        table = benchmark_layer(
            l1, l2,
            batch_sizes=(4,),
            names=["Fused-v1", "Fused-v2"],
            n_warmup=1, n_repeat=3,
        )
        assert table.rows[0].name == "Fused-v1"
        assert table.rows[1].name == "Fused-v2"
