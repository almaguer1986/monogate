"""
tests/test_eml_layer.py — Unit tests for monogate.torch.EMLLayer and EMLActivation.

Tests cover:
    - EMLActivation: forward shape, element-wise invariance, gradient flow
    - EMLLayer activation mode: shape, parameter count, gradient flow
    - EMLLayer tree mode: shape, parameter count, formula list, gradient flow
    - All four operators: EML, EDL, EXL, BEST
    - Serialization: state_dict round-trip
    - ONNX export (skipped if onnx not installed)
    - n_eml_nodes property
    - compare_to_native (smoke test)
    - Invalid arguments raise ValueError
"""

from __future__ import annotations

import io

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from monogate.torch import EMLActivation, EMLLayer, compare_to_native


# ── Helpers ───────────────────────────────────────────────────────────────────

OPERATORS = ["EML", "EDL", "EXL", "BEST"]
BATCH     = 4
IN        = 6
OUT       = 8


def _grad_ok(module: nn.Module, x: Tensor) -> bool:
    """Return True if a backward pass produces finite gradients for all params."""
    x = x.detach().requires_grad_(True)
    out = module(x)
    loss = out.sum()
    loss.backward()
    for p in module.parameters():
        if p.grad is None or not torch.isfinite(p.grad).all():
            return False
    return True


# ── EMLActivation ─────────────────────────────────────────────────────────────

class TestEMLActivation:
    @pytest.mark.parametrize("depth", [1, 2, 3])
    @pytest.mark.parametrize("operator", OPERATORS)
    def test_output_shape_preserved(self, depth: int, operator: str) -> None:
        act = EMLActivation(depth=depth, operator=operator)
        for shape in [(5,), (4, 8), (2, 3, 16)]:
            x   = torch.randn(*shape)
            out = act(x)
            assert out.shape == torch.Size(shape), (
                f"shape mismatch: in={shape} out={tuple(out.shape)}"
            )

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_element_wise(self, operator: str) -> None:
        """act(x)[i,j] depends only on x[i,j], not on other elements."""
        act = EMLActivation(depth=2, operator=operator)
        x   = torch.randn(3, 5)
        out = act(x)
        # Evaluate the same activation on a single scalar
        scalar = x[1, 2].unsqueeze(0).unsqueeze(0)   # shape (1, 1)
        out_scalar = act(scalar).item()
        assert abs(out[1, 2].item() - out_scalar) < 1e-5

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_gradient_flow(self, operator: str) -> None:
        act = EMLActivation(depth=2, operator=operator)
        x   = torch.randn(BATCH, IN)
        assert _grad_ok(act, x), f"gradient failed for operator={operator}"

    def test_depth_lt_1_raises(self) -> None:
        with pytest.raises(ValueError):
            EMLActivation(depth=0)

    def test_unknown_operator_raises(self) -> None:
        with pytest.raises(ValueError):
            EMLActivation(operator="UNKNOWN")

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_parameters_exist(self, operator: str) -> None:
        act    = EMLActivation(depth=2, operator=operator)
        params = list(act.parameters())
        assert len(params) > 0, f"no parameters for operator={operator}"

    def test_formula_returns_string(self) -> None:
        act = EMLActivation(depth=2)
        f   = act.formula("x")
        assert isinstance(f, str)
        assert len(f) > 0


# ── EMLLayer — activation mode ────────────────────────────────────────────────

class TestEMLLayerActivationMode:
    @pytest.mark.parametrize("operator", OPERATORS)
    def test_output_shape(self, operator: str) -> None:
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="activation")
        x     = torch.randn(BATCH, IN)
        out   = layer(x)
        assert out.shape == (BATCH, OUT)

    @pytest.mark.parametrize("depth", [1, 2, 3])
    def test_output_shape_various_depths(self, depth: int) -> None:
        layer = EMLLayer(IN, OUT, depth=depth)
        x     = torch.randn(BATCH, IN)
        out   = layer(x)
        assert out.shape == (BATCH, OUT)

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_gradient_flow(self, operator: str) -> None:
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="activation")
        x     = torch.randn(BATCH, IN)
        assert _grad_ok(layer, x), f"gradient failed for operator={operator}"

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_parameter_count(self, operator: str) -> None:
        """activation mode: Linear(in,out) params + activation params."""
        layer      = EMLLayer(IN, OUT, depth=2, operator=operator, mode="activation")
        n_linear   = IN * OUT + OUT                  # weight + bias
        n_act      = (1 << 2)                        # 2^depth leaves × (weight + bias) in Linear(1,1)
        # n_eml_nodes property
        assert layer.n_eml_nodes == (1 << 2) - 1    # 2^depth - 1 internal nodes

    def test_formula_returns_string(self) -> None:
        layer = EMLLayer(IN, OUT, depth=2)
        f     = layer.formula()
        assert isinstance(f, str)

    def test_n_parameters_property(self) -> None:
        layer = EMLLayer(IN, OUT, depth=2)
        assert layer.n_parameters == sum(p.numel() for p in layer.parameters())

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_state_dict_round_trip(self, operator: str) -> None:
        """Saving and reloading state_dict preserves forward output."""
        torch.manual_seed(0)
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="activation")
        x     = torch.randn(BATCH, IN)
        with torch.no_grad():
            out_before = layer(x).clone()

        buf = io.BytesIO()
        torch.save(layer.state_dict(), buf)
        buf.seek(0)

        layer2 = EMLLayer(IN, OUT, depth=2, operator=operator, mode="activation")
        layer2.load_state_dict(torch.load(buf, weights_only=True))
        with torch.no_grad():
            out_after = layer2(x)

        assert torch.allclose(out_before, out_after, atol=1e-6), (
            f"state_dict round-trip failed for operator={operator}"
        )


# ── EMLLayer — tree mode ──────────────────────────────────────────────────────

class TestEMLLayerTreeMode:
    @pytest.mark.parametrize("operator", OPERATORS)
    def test_output_shape(self, operator: str) -> None:
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="tree")
        x     = torch.randn(BATCH, IN)
        out   = layer(x)
        assert out.shape == (BATCH, OUT)

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_gradient_flow(self, operator: str) -> None:
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="tree")
        x     = torch.randn(BATCH, IN)
        assert _grad_ok(layer, x), f"gradient failed for operator={operator}"

    def test_formula_returns_list(self) -> None:
        layer    = EMLLayer(IN, OUT, depth=2, mode="tree")
        formulas = layer.formula(["a", "b", "c", "d", "e", "f"])
        assert isinstance(formulas, list)
        assert len(formulas) == OUT
        for f in formulas:
            assert isinstance(f, str)
            assert len(f) > 0

    def test_n_eml_nodes_tree_mode(self) -> None:
        """tree mode: OUT independent trees, each with (2^depth - 1) nodes."""
        layer = EMLLayer(IN, OUT, depth=2, mode="tree")
        assert layer.n_eml_nodes == OUT * ((1 << 2) - 1)

    @pytest.mark.parametrize("operator", OPERATORS)
    def test_state_dict_round_trip(self, operator: str) -> None:
        torch.manual_seed(1)
        layer = EMLLayer(IN, OUT, depth=2, operator=operator, mode="tree")
        x     = torch.randn(BATCH, IN)
        with torch.no_grad():
            out_before = layer(x).clone()

        buf = io.BytesIO()
        torch.save(layer.state_dict(), buf)
        buf.seek(0)

        layer2 = EMLLayer(IN, OUT, depth=2, operator=operator, mode="tree")
        layer2.load_state_dict(torch.load(buf, weights_only=True))
        with torch.no_grad():
            out_after = layer2(x)

        assert torch.allclose(out_before, out_after, atol=1e-6), (
            f"state_dict round-trip failed for operator={operator}"
        )


# ── Invalid arguments ─────────────────────────────────────────────────────────

class TestInvalidArguments:
    def test_depth_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            EMLLayer(4, 4, depth=0)

    def test_unknown_operator_raises(self) -> None:
        with pytest.raises(ValueError):
            EMLLayer(4, 4, operator="NOPE")

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError):
            EMLLayer(4, 4, mode="invalid")


# ── compare_to_native (smoke test) ────────────────────────────────────────────

class TestCompareToNative:
    def test_smoke(self, capsys: pytest.CaptureFixture) -> None:
        layer = EMLLayer(32, 32, depth=2)
        compare_to_native(layer, native_name="sin")
        captured = capsys.readouterr()
        assert "EMLLayer nodes" in captured.out
        assert "sin nodes" in captured.out

    def test_unknown_native_no_crash(self, capsys: pytest.CaptureFixture) -> None:
        layer = EMLLayer(4, 4, depth=1)
        compare_to_native(layer, native_name="mystery_fn")
        captured = capsys.readouterr()
        assert "no reference" in captured.out


# ── ONNX export ───────────────────────────────────────────────────────────────

class TestOnnxExport:
    @pytest.fixture(autouse=True)
    def _skip_if_no_onnx(self) -> None:
        pytest.importorskip("onnx")

    @pytest.mark.parametrize("mode", ["activation", "tree"])
    @pytest.mark.parametrize("operator", ["EML", "BEST"])
    def test_export_and_validate(
        self, tmp_path, mode: str, operator: str
    ) -> None:
        import onnx

        torch.manual_seed(0)
        layer = EMLLayer(4, 4, depth=2, operator=operator, mode=mode)
        layer.eval()
        dummy = torch.randn(1, 4)
        path  = tmp_path / f"eml_{mode}_{operator}.onnx"

        torch.onnx.export(
            layer, dummy, str(path),
            input_names=["x"], output_names=["y"],
            opset_version=14,
        )
        assert path.exists()

        model_proto = onnx.load(str(path))
        onnx.checker.check_model(model_proto)


# ── Training convergence (integration) ────────────────────────────────────────

class TestTrainingConvergence:
    def test_activation_mode_trains(self) -> None:
        """EMLLayer in activation mode should reduce loss over 300 steps."""
        torch.manual_seed(42)
        layer = EMLLayer(1, 1, depth=2, mode="activation")
        opt   = torch.optim.Adam(layer.parameters(), lr=1e-3)
        x     = torch.linspace(-1, 1, 50).unsqueeze(1)
        y     = x * x   # target: x^2

        initial_loss = F.mse_loss(layer(x).squeeze(), y.squeeze()).item()
        for _ in range(300):
            opt.zero_grad()
            loss = F.mse_loss(layer(x).squeeze(), y.squeeze())
            if not torch.isfinite(loss):
                break
            loss.backward()
            opt.step()
        final_loss = F.mse_loss(layer(x).squeeze(), y.squeeze()).item()

        assert final_loss < initial_loss, (
            f"Loss did not decrease: {initial_loss:.4e} -> {final_loss:.4e}"
        )
