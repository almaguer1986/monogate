"""Tests for the EDL operator and Operator abstraction."""
import cmath
import math

import pytest
import torch

from monogate.core import (
    EDL, EML, EMN, EXL, EAL, EDL_NEG_ONE, EDL_ONE, Operator,
    div_edl, exp_edl, ln_edl, make_exp, make_ln, mul_edl, neg_edl, pow_edl, recip_edl,
    ln_eml, pow_eml, pow_exl,
    HybridOperator, BEST,
)
from monogate.torch_ops import edl_op, edl_op_safe, EDL_SAFE_CONSTANT, exl_op, eal_op
from monogate.network import EMLNetwork, HybridNetwork


# ── Operator class ────────────────────────────────────────────────────────────

def test_operator_has_name():
    assert EML.name == "EML"
    assert EDL.name == "EDL"


def test_eml_constant():
    assert EML.constant == 1.0 + 0j


def test_edl_constant():
    assert abs(EDL.constant - cmath.e) < 1e-14


def test_operator_repr():
    assert "EML" in repr(EML)
    assert "EDL" in repr(EDL)


# ── EDL gate (Python / cmath) ─────────────────────────────────────────────────

def test_edl_fundamental_identity():
    # edl(x, e) = exp(x) — EDL's natural identity (ln(e)=1)
    x = 1.5
    result = EDL.func(x, cmath.e)
    assert abs(result - cmath.exp(x)) < 1e-14


def test_edl_various_inputs():
    # edl(0, e) = exp(0)/ln(e) = 1/1 = 1
    assert abs(EDL.func(0, cmath.e) - 1.0) < 1e-14
    # edl(1, e²) = exp(1)/ln(e²) = e/2
    e2 = cmath.e ** 2
    assert abs(EDL.func(1, e2) - cmath.e / 2) < 1e-14


def test_edl_domain_error_y_equals_1():
    with pytest.raises(ValueError, match="EDL domain error"):
        EDL.func(0, 1)


def test_edl_domain_error_y_equals_0():
    with pytest.raises(ValueError, match="EDL domain error"):
        EDL.func(0, 0)


# ── EML gate unchanged ────────────────────────────────────────────────────────

def test_eml_func_smoke():
    # eml(1, 1) = e^1 - ln(1) = e
    result = EML.func(1, 1)
    assert abs(result - cmath.e) < 1e-14


def test_eml_op_unchanged():
    # Existing op() function still works — regression guard
    from monogate import op
    assert abs(op(1, 1) - math.e) < 1e-14


# ── EDL tensor op ─────────────────────────────────────────────────────────────

def test_edl_op_tensor_identity():
    # edl_op(x, e) ≈ exp(x)
    x = torch.tensor(1.5)
    e = torch.tensor(math.e)
    result = edl_op(x, e)
    assert abs(result.item() - math.exp(1.5)) < 1e-6


def test_edl_op_tensor_batch():
    x = torch.tensor([0.0, 1.0, 2.0])
    e = torch.full_like(x, math.e)
    result = edl_op(x, e)
    expected = torch.exp(x)
    assert torch.allclose(result, expected, atol=1e-6)


def test_edl_op_tensor_gradients():
    # Gradients must flow through edl_op
    x = torch.tensor(1.0, requires_grad=True)
    y = torch.tensor(math.e, requires_grad=True)
    out = edl_op(x, y)
    out.backward()
    assert x.grad is not None
    assert y.grad is not None


# ── EMLTree with op_func=edl_op ───────────────────────────────────────────────

def test_emltree_edl_forward():
    from monogate.network import EMLTree
    model = EMLTree(depth=1, op_func=edl_op)
    out = model()
    assert torch.isfinite(out)


def test_emltree_default_still_eml():
    from monogate.network import EMLTree
    model = EMLTree(depth=1)
    out = model()
    assert torch.isfinite(out)


# ── EMLNetwork with op_func=edl_op ────────────────────────────────────────────

def test_emlnetwork_edl_forward():
    from monogate.network import EMLNetwork
    model = EMLNetwork(in_features=1, depth=1, op_func=edl_op)
    x = torch.ones(4, 1)
    out = model(x)
    assert out.shape == (4,)
    assert torch.all(torch.isfinite(out))


# ── make_exp / make_ln ────────────────────────────────────────────────────────

def test_make_exp_eml():
    f = make_exp(EML)
    assert abs(f(1.5) - cmath.exp(1.5)) < 1e-12


def test_make_exp_edl():
    f = make_exp(EDL)
    assert abs(f(1.5) - cmath.exp(1.5)) < 1e-12


def test_exp_edl_singleton():
    assert abs(exp_edl(0) - 1.0) < 1e-14
    assert abs(exp_edl(1) - cmath.e) < 1e-14


def test_make_ln_eml():
    f = make_ln(EML)
    assert abs(f(math.e) - 1.0) < 1e-12
    assert abs(f(1) - 0.0) < 1e-12
    assert abs(f(2) - math.log(2)) < 1e-12


def test_make_ln_edl():
    # 3-node formula: edl(0, edl(edl(0, x), e))
    f = make_ln(EDL)
    assert abs(f(math.e) - 1.0) < 1e-12
    assert abs(f(2) - math.log(2)) < 1e-12
    assert abs(f(10) - math.log(10)) < 1e-12


def test_ln_edl_singleton():
    assert abs(ln_edl(math.e) - 1.0) < 1e-12
    assert abs(ln_edl(2) - math.log(2)) < 1e-12


def test_ln_is_inverse_of_exp_eml():
    f_exp = make_exp(EML)
    f_ln  = make_ln(EML)
    for x in (0.5, 1.0, 2.0, 3.7):
        assert abs(f_ln(f_exp(x)) - x) < 1e-10


def test_ln_is_inverse_of_exp_edl():
    f_exp = make_exp(EDL)
    f_ln  = make_ln(EDL)
    for x in (0.5, 1.0, 2.0, 3.7):
        assert abs(f_ln(f_exp(x)) - x) < 1e-10


def test_make_ln_unknown_operator_raises():
    other = Operator("OTHER", lambda x, y: x + y, 0j)
    with pytest.raises(NotImplementedError):
        make_ln(other)


# ── div_edl ───────────────────────────────────────────────────────────────────

def test_div_edl_basic():
    # edl(ln(x), exp(y)) = x / y
    assert abs(div_edl(6 + 0j, 3 + 0j) - 2.0) < 1e-12
    assert abs(div_edl(5 + 0j, 2 + 0j) - 2.5) < 1e-12


def test_div_edl_matches_true_division():
    # Note: x=1 excluded — ln_edl(1) hits the EDL singularity in the intermediate
    # step edl(0, 1).  Mathematically ln(1)=0 but the 3-node formula can't reach it.
    for x, y in [(10, 4), (7, 3), (2, 5), (2.5, 0.5)]:
        result = div_edl(complex(x), complex(y))
        assert abs(result - x / y) < 1e-10, f"div_edl({x},{y}) = {result}, expected {x/y}"


def test_div_edl_is_not_subtraction():
    # Direct proof that the "sub" parallel does NOT give subtraction for EDL
    result = div_edl(5 + 0j, 2 + 0j)
    assert abs(result - 2.5) < 1e-12   # = 5/2
    assert abs(result - 3.0) > 0.1     # NOT 5-2


# ── recip_edl ─────────────────────────────────────────────────────────────────

def test_recip_edl_basic():
    assert abs(recip_edl(2 + 0j) - 0.5) < 1e-12
    assert abs(recip_edl(4 + 0j) - 0.25) < 1e-12
    assert abs(recip_edl(10 + 0j) - 0.1) < 1e-12


def test_recip_edl_self_inverse():
    for x in (2.0, 5.0, 0.3, 7.5):
        assert abs(recip_edl(recip_edl(complex(x))) - x) < 1e-10


def test_recip_edl_consistent_with_div():
    # 1/x = div_edl(1, x) is NOT available via the ln_edl path (hits singularity),
    # but recip_edl bypasses that by using edl(0, edl(x, e)) directly.
    # Confirm recip_edl agrees with plain Python division.
    for x in (2.5, 3.0, 0.7):
        assert abs(recip_edl(complex(x)) - 1/x) < 1e-12


# ── neg_edl ───────────────────────────────────────────────────────────────────

def test_neg_edl_basic():
    assert abs(neg_edl(2 + 0j) - (-2)) < 1e-12
    assert abs(neg_edl(5 + 0j) - (-5)) < 1e-12
    assert abs(neg_edl(0.5 + 0j) - (-0.5)) < 1e-12


def test_neg_edl_double_negation():
    for x in (2.0, 3.7, 0.4):
        # neg_edl(-x) requires x<0 which hits domain issues; test x>1 roundtrip
        # via neg_edl(neg_edl(x)) — but neg_edl(x)<0 so ln_edl fails on that.
        # Instead confirm neg_edl(-neg_edl(x)) = x using recip and a workaround.
        neg_x = neg_edl(complex(x))
        # -(-x) = x: use div_edl(neg_x, EDL_NEG_ONE)
        # div_edl(-x, -1) = -x / -1 = x
        back = div_edl(neg_x, EDL_NEG_ONE)
        assert abs(back - x) < 1e-10, f"round-trip failed for x={x}: got {back}"


# ── EDL constants ─────────────────────────────────────────────────────────────

def test_edl_one():
    assert abs(EDL_ONE - 1.0) < 1e-14


def test_edl_neg_one():
    assert abs(EDL_NEG_ONE - (-1.0)) < 1e-14


def test_edl_neg_one_via_neg_edl():
    # neg_edl applied to EDL_ONE should give EDL_NEG_ONE
    # but EDL_ONE = 1 and ln_edl(1) hits the singularity — confirms the dead zone
    import pytest
    with pytest.raises(ValueError, match="EDL domain error"):
        neg_edl(EDL_ONE)


# ── mul_edl ───────────────────────────────────────────────────────────────────

def test_mul_edl_integers():
    assert abs(mul_edl(3 + 0j, 4 + 0j) - 12) < 1e-10
    assert abs(mul_edl(2 + 0j, 5 + 0j) - 10) < 1e-10


def test_mul_edl_fractions():
    assert abs(mul_edl(6 + 0j, 0.5 + 0j) - 3.0) < 1e-10
    assert abs(mul_edl(2.5 + 0j, 4.0 + 0j) - 10.0) < 1e-10


def test_mul_edl_identity():
    # x * 1 = x  (but x=1 is a domain hole for ln_edl, so test x=e)
    assert abs(mul_edl(math.e + 0j, 1.0 + 0j) - math.e) < 1e-10


def test_mul_edl_commutative():
    for x, y in [(3, 4), (2.5, 1.5), (7, 0.2)]:
        assert abs(mul_edl(complex(x), complex(y)) - mul_edl(complex(y), complex(x))) < 1e-10


def test_mul_edl_consistent_with_div():
    # x * y / y = x
    for x, y in [(6, 3), (5, 2), (10, 4)]:
        product = mul_edl(complex(x), complex(y))
        back = div_edl(product, complex(y))
        assert abs(back - x) < 1e-9, f"round-trip failed: x={x}, y={y}"


# ── pow_edl ───────────────────────────────────────────────────────────────────

def test_pow_edl_square():
    assert abs(pow_edl(3 + 0j, 2) - 9) < 1e-9
    assert abs(pow_edl(4 + 0j, 2) - 16) < 1e-9


def test_pow_edl_half():
    assert abs(pow_edl(9 + 0j, 0.5) - 3) < 1e-9
    assert abs(pow_edl(4 + 0j, 0.5) - 2) < 1e-9


def test_pow_edl_matches_math():
    for x, n in [(2, 10), (3, 3), (5, 0.5), (math.e, 2)]:
        result = pow_edl(complex(x), n)
        assert abs(result - x**n) < 1e-8, f"pow_edl({x},{n})={result}, expected {x**n}"


# ── add_edl not possible ──────────────────────────────────────────────────────

def test_add_edl_raises():
    from monogate.core import add_edl
    with pytest.raises(NotImplementedError):
        add_edl(3 + 0j, 4 + 0j)


# ── compare_op ────────────────────────────────────────────────────────────────

def test_compare_op_runs(capsys):
    from monogate.core import compare_op
    compare_op("test", lambda x: x**2, lambda x: x**2, [1.0, 2.0, 3.0])
    out = capsys.readouterr().out
    assert "test" in out
    assert "err" in out


# ── domain advantage: pow_edl handles x < 1 where pow_eml fails ──────────────

def test_pow_edl_x_less_than_1():
    # pow_eml(0.5, 10) fails: internally needs ln_eml(ln(0.5)) = ln(-0.693) -> domain error
    # pow_edl(0.5, 10) works: uses cmath throughout, handles negative intermediates
    result = pow_edl(0.5 + 0j, 10)
    assert abs(result.real - 0.5**10) < 1e-15


def test_pow_eml_fails_on_x_less_than_1():
    with pytest.raises(ValueError):
        pow_eml(0.5, 10)


# ── ln_edl overflow dead zone ─────────────────────────────────────────────────

def test_ln_edl_works_away_from_one():
    assert abs(ln_edl(1.01 + 0j).real - math.log(1.01)) < 1e-10
    assert abs(ln_edl(0.99 + 0j).real - math.log(0.99)) < 1e-10


def test_ln_edl_dead_zone_near_one():
    # x = 1.001: ln(1.001) ≈ 0.001, so 1/ln(x) ≈ 1000 -> exp(1000) overflows
    with pytest.raises((OverflowError, ValueError)):
        ln_edl(1.001 + 0j)


def test_ln_eml_handles_near_one():
    # EML ln has no overflow dead zone — works fine arbitrarily close to 1
    assert abs(ln_eml(1.001) - math.log(1.001)) < 1e-10
    assert abs(ln_eml(1.0001) - math.log(1.0001)) < 1e-10


# ── deep-chain stability: x^50 relative error ────────────────────────────────

def _chain_mul(fn, x, n):
    acc = x
    for _ in range(n - 1):
        acc = fn(acc, x)
    return acc

def test_mul_edl_chain_rel_error():
    # 49-step chain: x^50 should match math.pow to ~1e-12 relative error
    for x in [1.1, 1.5, 2.0]:
        result = _chain_mul(mul_edl, complex(x), 50).real
        ref    = x ** 50
        rel    = abs(result - ref) / ref
        assert rel < 1e-12, f"chain_edl({x},50) relative error {rel:.2e} exceeds 1e-12"


# ── Operator.exp / Operator.ln methods ───────────────────────────────────────

def test_operator_exp_eml():
    assert abs(EML.exp(1 + 0j).real - math.e) < 1e-14

def test_operator_ln_eml():
    assert abs(EML.ln(math.e + 0j).real - 1.0) < 1e-10

def test_operator_exp_edl():
    assert abs(EDL.exp(1 + 0j).real - math.e) < 1e-14

def test_operator_ln_edl():
    assert abs(EDL.ln(math.e + 0j).real - 1.0) < 1e-10

def test_operator_exp_emn_raises():
    with pytest.raises(NotImplementedError):
        EMN.exp(1 + 0j)

def test_operator_ln_emn_raises():
    with pytest.raises(NotImplementedError):
        EMN.ln(math.e + 0j)


# ── Operator attribute dispatch (__getattr__ / register) ─────────────────────

def test_eml_mul_via_attr():
    assert abs(EML.mul(2.0, 3.0) - 6.0) < 1e-10

def test_eml_div_via_attr():
    assert abs(EML.div(6.0, 3.0) - 2.0) < 1e-10

def test_eml_pow_via_attr():
    assert abs(EML.pow(2.0, 10.0) - 1024.0) < 1e-6

def test_eml_ops_list():
    ops = EML.ops()
    assert 'mul' in ops
    assert 'div' in ops
    assert 'add' in ops
    assert 'neg' in ops
    assert 'pow' in ops
    assert 'recip' in ops
    assert 'sub' in ops

def test_edl_mul_via_attr():
    assert abs(EDL.mul(2 + 0j, 3 + 0j).real - 6.0) < 1e-10

def test_edl_div_via_attr():
    assert abs(EDL.div(6 + 0j, 2 + 0j).real - 3.0) < 1e-10

def test_edl_ops_list():
    ops = EDL.ops()
    assert 'mul' in ops
    assert 'div' in ops
    assert 'recip' in ops

def test_unknown_op_raises_attribute_error():
    with pytest.raises(AttributeError, match="no registered operation"):
        EML.nonexistent_op

def test_register_custom_op():
    EML.register('_test_identity', lambda x: x)
    assert EML._test_identity(42.0) == 42.0
    del EML._ops['_test_identity']  # clean up


# ── EMN operator ─────────────────────────────────────────────────────────────

def test_emn_gate_is_negated_eml():
    # emn(x, y) = ln(y) - exp(x) = -eml(x, y)
    from monogate.core import _emn_func, _eml_func
    x, y = 1.5 + 0j, 2.0 + 0j
    assert abs(_emn_func(x, y) + _eml_func(x, y)) < 1e-14

def test_emn_natural_output_is_neg_exp():
    # emn(x, 1) = ln(1) - exp(x) = -exp(x)
    for x in [0.0, 1.0, -1.0]:
        result = EMN.func(x + 0j, 1.0 + 0j).real
        assert abs(result + math.exp(x)) < 1e-14

def test_emn_neg_exp_registered():
    assert abs(EMN.neg_exp(0 + 0j).real - (-1.0)) < 1e-14
    assert abs(EMN.neg_exp(1 + 0j).real - (-math.e)) < 1e-14

def test_emn_ln_shift_registered():
    # ln_shift(y) = ln(y) - 1
    assert abs(EMN.ln_shift(math.e + 0j).real - 0.0) < 1e-14
    assert abs(EMN.ln_shift(1.0 + 0j).real - (-1.0)) < 1e-14

def test_emn_repr():
    assert "EMN" in repr(EMN)

def test_emn_ops_list():
    assert 'neg_exp' in EMN.ops()
    assert 'ln_shift' in EMN.ops()


# ── EXL operator: exp(x)*ln(y) ────────────────────────────────────────────────

def test_exl_exp_is_1_node():
    # exl(x, e) = exp(x)*ln(e) = exp(x)*1 = exp(x)
    assert abs(EXL.exp(1 + 0j).real - math.e) < 1e-14
    assert abs(EXL.exp(0 + 0j).real - 1.0) < 1e-14

def test_exl_ln_is_1_node():
    # exl(0, x) = exp(0)*ln(x) = ln(x)  — 1-node formula, no dead zone
    assert abs(EXL.ln(math.e + 0j).real - 1.0) < 1e-14
    assert abs(EXL.ln(2.0 + 0j).real - math.log(2)) < 1e-14
    assert abs(EXL.ln(0.5 + 0j).real - math.log(0.5)) < 1e-14

def test_exl_ln_no_dead_zone_near_one():
    # EXL ln has NO dead zone (direct cmath.log) — contrast with EDL
    for x in [1.0001, 0.9999, 1.001, 0.999]:
        got = EXL.ln(x + 0j).real
        ref = math.log(x)
        assert abs(got - ref) < 1e-12, f"EXL.ln({x}) err={abs(got-ref):.2e}"

def test_exl_ln_vs_edl_dead_zone():
    # EDL ln overflows near x=1; EXL ln does not
    import pytest
    with pytest.raises((OverflowError, ValueError)):
        ln_edl(1.001 + 0j)
    # EXL handles the same value fine
    assert abs(EXL.ln(1.001 + 0j).real - math.log(1.001)) < 1e-12

def test_exl_make_exp():
    fn = make_exp(EXL)
    assert abs(fn(1 + 0j).real - math.e) < 1e-14

def test_exl_make_ln():
    fn = make_ln(EXL)
    assert abs(fn(math.e + 0j).real - 1.0) < 1e-14
    assert abs(fn(2.0 + 0j).real - math.log(2)) < 1e-14

def test_pow_exl_integer():
    assert abs(pow_exl(2 + 0j, 10 + 0j).real - 1024.0) < 1e-9
    assert abs(pow_exl(3 + 0j, 3 + 0j).real - 27.0) < 1e-9

def test_pow_exl_fractional():
    assert abs(pow_exl(4 + 0j, 0.5 + 0j).real - 2.0) < 1e-10

def test_pow_exl_x_less_than_1():
    # EXL can handle x<1 (complex arithmetic)
    result = pow_exl(0.5 + 0j, 2 + 0j).real
    assert abs(result - 0.25) < 1e-12

def test_exl_pow_registered():
    result = EXL.pow(2 + 0j, 8 + 0j).real
    assert abs(result - 256.0) < 1e-9

def test_exl_ops_list():
    assert 'pow' in EXL.ops()

def test_exl_repr():
    assert "EXL" in repr(EXL)


# ── EAL operator: exp(x)+ln(y) ────────────────────────────────────────────────

def test_eal_exp_is_1_node():
    # eal(x, 1) = exp(x) + ln(1) = exp(x) + 0 = exp(x)
    assert abs(EAL.exp(1 + 0j).real - math.e) < 1e-14
    assert abs(EAL.exp(0 + 0j).real - 1.0) < 1e-14

def test_eal_shifted_ln():
    # eal(0, x) = 1 + ln(x) — NOT bare ln, shifted by 1
    assert abs(EAL.func(0j, math.e + 0j).real - 2.0) < 1e-14   # 1 + ln(e) = 2
    assert abs(EAL.func(0j, 1.0 + 0j).real - 1.0) < 1e-14     # 1 + ln(1) = 1

def test_eal_make_exp():
    fn = make_exp(EAL)
    assert abs(fn(0 + 0j).real - 1.0) < 1e-14

def test_eal_make_ln_raises():
    with pytest.raises(NotImplementedError, match="EAL"):
        make_ln(EAL)

def test_eal_ln_method_raises():
    with pytest.raises(NotImplementedError):
        EAL.ln(math.e + 0j)

def test_eal_ops_list_empty():
    # No arithmetic operations registered for EAL
    assert EAL.ops() == []

def test_eal_repr():
    assert "EAL" in repr(EAL)


# ── Operator.benchmark() ─────────────────────────────────────────────────────

def test_benchmark_eml_returns_dict():
    bm = EML.benchmark()
    assert isinstance(bm, dict)
    assert 'exp_max_err' in bm
    assert 'ln_max_err' in bm
    assert 'complete' in bm

def test_benchmark_eml_accuracy():
    bm = EML.benchmark()
    assert bm['exp_max_err'] < 1e-12
    assert bm['ln_max_err'] < 1e-12
    assert bm['complete'] is True

def test_benchmark_edl_accuracy():
    bm = EDL.benchmark()
    assert bm['exp_max_err'] < 1e-12
    assert bm['ln_max_err'] < 1e-12
    assert bm['complete'] is True

def test_benchmark_exl_exp_ok_ln_ok():
    bm = EXL.benchmark()
    assert bm['exp_max_err'] < 1e-12
    assert bm['ln_max_err'] < 1e-12  # EXL has 1-node ln
    assert bm['complete'] is False

def test_benchmark_emn_exp_and_ln_none():
    bm = EMN.benchmark()
    assert bm['exp_max_err'] is None
    assert bm['ln_max_err'] is None
    assert bm['complete'] is False

def test_benchmark_eal_ln_none():
    bm = EAL.benchmark()
    assert bm['exp_max_err'] < 1e-12  # EAL has 1-node exp
    assert bm['ln_max_err'] is None
    assert bm['complete'] is False

def test_benchmark_ops_list():
    bm = EML.benchmark()
    assert 'mul' in bm['ops']
    assert 'div' in bm['ops']


# ── Operator.info() ──────────────────────────────────────────────────────────

def test_info_eml_prints(capsys):
    EML.info()
    out = capsys.readouterr().out
    assert "EML" in out
    assert "exp(x) - ln(y)" in out
    assert "YES" in out  # Complete

def test_info_edl_prints(capsys):
    EDL.info()
    out = capsys.readouterr().out
    assert "EDL" in out
    assert "Complete" in out

def test_info_exl_not_complete(capsys):
    EXL.info()
    out = capsys.readouterr().out
    assert "NO" in out

def test_info_emn_na(capsys):
    EMN.info()
    out = capsys.readouterr().out
    assert "EMN" in out
    assert "N/A" in out  # exp/ln both unavailable


# ── operators.py module ──────────────────────────────────────────────────────

def test_all_operators_list():
    from monogate.operators import ALL_OPERATORS
    names = [o.name for o in ALL_OPERATORS]
    assert "EML" in names
    assert "EDL" in names
    assert "EXL" in names
    assert "EAL" in names
    assert "EMN" in names

def test_complete_operators_list():
    from monogate.operators import COMPLETE_OPERATORS
    names = [o.name for o in COMPLETE_OPERATORS]
    assert "EML" in names
    assert "EDL" in names
    assert "EXL" not in names
    assert "EMN" not in names

def test_get_operator_eml():
    from monogate.operators import get_operator
    op = get_operator("EML")
    assert op.name == "EML"

def test_get_operator_unknown_raises():
    from monogate.operators import get_operator
    with pytest.raises(KeyError, match="Unknown operator"):
        get_operator("UNKNOWN")

def test_compare_all_runs(capsys):
    from monogate.operators import compare_all
    compare_all()
    out = capsys.readouterr().out
    assert "EML" in out
    assert "EDL" in out
    assert "exp(x)" in out

def test_compare_all_custom_operators(capsys):
    from monogate.operators import compare_all
    compare_all([EML, EDL])
    out = capsys.readouterr().out
    assert "EML" in out
    assert "EDL" in out
    assert "EXL" not in out

def test_markdown_table_returns_string():
    from monogate.operators import markdown_table
    md = markdown_table()
    assert isinstance(md, str)
    assert "| Function |" in md
    assert "EML" in md
    assert "EDL" in md

def test_markdown_table_has_complete_row():
    from monogate.operators import markdown_table
    md = markdown_table()
    assert "Complete?" in md
    assert "**YES**" in md

def test_markdown_table_custom_operators():
    from monogate.operators import markdown_table
    md = markdown_table([EML, EDL])
    assert "EML" in md
    assert "EDL" in md
    assert "EXL" not in md

def test_operators_importable_from_top():
    from monogate import ALL_OPERATORS, COMPLETE_OPERATORS, get_operator, compare_all, markdown_table
    assert len(ALL_OPERATORS) == 5
    assert len(COMPLETE_OPERATORS) == 2


# ── exl_op / eal_op tensor operations ────────────────────────────────────────

def test_exl_op_exp_identity():
    # exl(x, e) = exp(x)*ln(e) = exp(x)
    x = torch.tensor(1.5)
    e = torch.tensor(math.e)
    result = exl_op(x, e)
    assert abs(result.item() - math.exp(1.5)) < 1e-6

def test_exl_op_ln_identity():
    # exl(0, y) = exp(0)*ln(y) = ln(y)
    y = torch.tensor(math.e)
    result = exl_op(torch.tensor(0.0), y)
    assert abs(result.item() - 1.0) < 1e-6

def test_exl_op_pow():
    # exl(exl(exl(0,n), x), e) = x^n
    x = torch.tensor(2.0)
    n = torch.tensor(3.0)
    e = torch.tensor(math.e)
    step1 = exl_op(torch.tensor(0.0), n)         # ln(n)
    step2 = exl_op(step1, x)                      # n*ln(x)
    step3 = exl_op(step2, e)                      # exp(n*ln(x)) = x^n
    assert abs(step3.item() - 8.0) < 1e-5

def test_exl_op_gradient_flows():
    x = torch.tensor(1.5, requires_grad=True)
    y = torch.tensor(math.e, requires_grad=True)
    result = exl_op(x, y)
    result.backward()
    # d/dx [exp(x)*ln(y)] = exp(x)*ln(y) = result
    assert abs(x.grad.item() - result.item()) < 1e-5
    # d/dy [exp(x)*ln(y)] = exp(x)/y
    expected_dy = math.exp(1.5) / math.e
    assert abs(y.grad.item() - expected_dy) < 1e-5

def test_eal_op_exp_identity():
    # eal(x, 1) = exp(x) + ln(1) = exp(x)
    x = torch.tensor(1.5)
    result = eal_op(x, torch.tensor(1.0))
    assert abs(result.item() - math.exp(1.5)) < 1e-6

def test_eal_op_shifted_ln():
    # eal(0, y) = 1 + ln(y)
    y = torch.tensor(math.e)
    result = eal_op(torch.tensor(0.0), y)
    assert abs(result.item() - 2.0) < 1e-6  # 1 + ln(e) = 2

def test_eal_op_gradient_flows():
    x = torch.tensor(1.0, requires_grad=True)
    y = torch.tensor(math.e, requires_grad=True)
    result = eal_op(x, y)
    result.backward()
    # d/dx = exp(x)
    assert abs(x.grad.item() - math.e) < 1e-5
    # d/dy = 1/y
    assert abs(y.grad.item() - 1.0 / math.e) < 1e-5

def test_exl_op_batch():
    x = torch.tensor([0.0, 1.0, 2.0])
    y = torch.tensor([math.e, math.e, math.e])
    result = exl_op(x, y)
    expected = torch.tensor([1.0, math.e, math.e**2])
    assert torch.allclose(result, expected, atol=1e-5)

def test_eal_op_batch():
    x = torch.zeros(3)
    y = torch.tensor([1.0, math.e, math.e**2])
    result = eal_op(x, y)
    expected = torch.tensor([1.0, 2.0, 3.0])
    assert torch.allclose(result, expected, atol=1e-5)


# ── edl_op_safe ───────────────────────────────────────────────────────────────

def test_edl_op_safe_exp_identity():
    # edl_safe(x, e-1) = exp(x)/ln((e-1)+1) = exp(x)/ln(e) = exp(x)
    x = torch.tensor(1.5)
    c = torch.tensor(EDL_SAFE_CONSTANT)
    result = edl_op_safe(x, c)
    assert abs(result.item() - math.exp(1.5)) < 1e-5

def test_edl_op_safe_never_nan_near_one():
    # Plain edl_op explodes when y=1; edl_op_safe must be finite there
    x = torch.zeros(10)
    y = torch.ones(10)   # ln(1)=0, plain EDL -> inf/nan
    result_safe = edl_op_safe(x, y)
    assert torch.isfinite(result_safe).all(), "edl_op_safe must stay finite at y=1"

def test_edl_op_safe_finite_across_softplus_range():
    # Simulate what softplus outputs: values in ~[0.3, 3.0]
    x = torch.zeros(100)
    y = torch.linspace(0.3, 3.0, 100)  # softplus output range
    result = edl_op_safe(x, y)
    assert torch.isfinite(result).all()

def test_edl_op_safe_gradient_flows():
    x = torch.tensor(1.0, requires_grad=True)
    y = torch.tensor(EDL_SAFE_CONSTANT, requires_grad=True)
    result = edl_op_safe(x, y)
    result.backward()
    assert x.grad is not None and torch.isfinite(x.grad)
    assert y.grad is not None and torch.isfinite(y.grad)

def test_edl_op_safe_constant_value():
    # EDL_SAFE_CONSTANT = e - 1
    assert abs(EDL_SAFE_CONSTANT - (math.e - 1)) < 1e-12

def test_edl_op_safe_trains_without_nan():
    # A simple 1-step training loop must not produce NaN
    import torch.nn.functional as F
    from monogate.network import EMLNetwork
    torch.manual_seed(0)
    model = EMLNetwork(in_features=1, depth=3, op_func=edl_op_safe)
    x = torch.linspace(-2.0, 2.0, 32).unsqueeze(1)
    y = torch.sin(x.squeeze())
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    losses = []
    for _ in range(20):
        opt.zero_grad()
        pred = model(x)
        loss = F.mse_loss(pred, y)
        if torch.isfinite(loss):
            loss.backward()
            opt.step()
            losses.append(loss.item())
    assert len(losses) > 0, "edl_op_safe: all training steps produced NaN"
    assert all(math.isfinite(v) for v in losses)


# ── HybridNetwork ─────────────────────────────────────────────────────────────

def test_hybrid_network_forward():
    torch.manual_seed(0)
    model = HybridNetwork(in_features=1, depth=3)
    x = torch.linspace(0.5, 2.0, 16).unsqueeze(1)
    out = model(x)
    assert out.shape == (16,)

def test_hybrid_network_finite_output():
    # HybridNetwork should produce finite outputs on a safe input range
    torch.manual_seed(42)
    model = HybridNetwork(in_features=1, depth=3)
    x = torch.linspace(0.5, 2.0, 64).unsqueeze(1)
    out = model(x)
    assert torch.isfinite(out).all(), "HybridNetwork should be finite on [0.5, 2.0]"

def test_hybrid_network_trains():
    import torch.nn.functional as F
    torch.manual_seed(0)
    model = HybridNetwork(in_features=1, depth=3)
    x = torch.linspace(0.1, 3.0, 64).unsqueeze(1)
    y = torch.sin(x.squeeze())
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    losses = []
    for _ in range(30):
        opt.zero_grad()
        pred = model(x)
        loss = F.mse_loss(pred, y)
        if torch.isfinite(loss):
            loss.backward()
            import torch.nn as nn
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            losses.append(loss.item())
    assert len(losses) >= 25, f"HybridNetwork: too many NaN steps ({30 - len(losses)})"

def test_hybrid_network_custom_ops():
    from monogate.torch_ops import eal_op
    torch.manual_seed(1)
    model = HybridNetwork(in_features=1, depth=2, inner_op=eal_op, outer_op=exl_op)
    x = torch.ones(4, 1)
    out = model(x)
    assert out.shape == (4,)

def test_hybrid_network_depth_one():
    # depth=1: one root EML node, two linear leaves
    torch.manual_seed(0)
    model = HybridNetwork(in_features=1, depth=1)
    x = torch.ones(8, 1)
    out = model(x)
    assert out.shape == (8,)

def test_hybrid_network_depth_zero_raises():
    with pytest.raises(ValueError, match="depth >= 1"):
        HybridNetwork(in_features=1, depth=0)

def test_hybrid_vs_eml_stability():
    # Hybrid should have better finite-output rate than plain EMLNetwork
    # on random init (random leaves Normal(0,0.5))
    x = torch.linspace(0.1, 3.0, 64).unsqueeze(1)
    eml_ok = hybrid_ok = 0
    for seed in range(20):
        torch.manual_seed(seed)
        m_eml = EMLNetwork(in_features=1, depth=4)
        m_hyb = HybridNetwork(in_features=1, depth=4)
        for m in [m_eml, m_hyb]:
            with torch.no_grad():
                for p in m.parameters():
                    p.data.normal_(0.0, 0.5)
        with torch.no_grad():
            o_eml = m_eml(x)
            o_hyb = m_hyb(x)
        if torch.isfinite(o_eml).all():
            eml_ok += 1
        if torch.isfinite(o_hyb).all():
            hybrid_ok += 1
    assert hybrid_ok >= eml_ok, (
        f"HybridNetwork should be >= EMLNetwork stability "
        f"(hybrid {hybrid_ok}/20, eml {eml_ok}/20)"
    )


# ── HybridOperator ────────────────────────────────────────────────────────────

def test_hybrid_operator_pow_uses_exl():
    # BEST.pow must use pow_exl (EXL-routed)
    result = BEST.pow(2.0 + 0j, 10.0 + 0j)
    assert abs(result.real - 1024.0) < 1e-6

def test_hybrid_operator_div_uses_edl():
    result = BEST.div(6.0 + 0j, 2.0 + 0j)
    assert abs(result.real - 3.0) < 1e-9

def test_hybrid_operator_mul_uses_edl():
    result = BEST.mul(3.0 + 0j, 4.0 + 0j)
    assert abs(result.real - 12.0) < 1e-9

def test_hybrid_operator_add_uses_eml():
    result = BEST.add(3.0, 4.0)
    assert abs(result - 7.0) < 1e-9

def test_hybrid_operator_sub_uses_eml():
    result = BEST.sub(5.0, 2.0)
    assert abs(result - 3.0) < 1e-9

def test_hybrid_operator_ln_uses_exl_no_dead_zone():
    # EXL.ln has no dead zone near x=1 (unlike EDL)
    for x in [1.001, 0.999, 1.0001]:
        result = BEST.ln(x + 0j)
        assert abs(result.real - math.log(x)) < 1e-10

def test_hybrid_operator_exp():
    assert abs(BEST.exp(1 + 0j).real - math.e) < 1e-12

def test_hybrid_operator_recip():
    result = BEST.recip(2.0 + 0j)
    assert abs(result.real - 0.5) < 1e-9

def test_hybrid_operator_neg():
    result = BEST.neg(3.0 + 0j)
    assert abs(result.real - (-3.0)) < 1e-9

def test_hybrid_operator_ops_list():
    ops = BEST.ops()
    for name in ['exp', 'ln', 'pow', 'mul', 'div', 'recip', 'neg', 'sub', 'add']:
        assert name in ops

def test_hybrid_operator_unknown_raises():
    with pytest.raises(AttributeError, match="no routing for"):
        BEST.sqrt

def test_hybrid_operator_custom_routing():
    custom = HybridOperator({'pow': EXL, 'add': EML}, name="custom")
    assert abs(custom.pow(2.0 + 0j, 3.0 + 0j).real - 8.0) < 1e-9
    assert abs(custom.add(1.0, 2.0) - 3.0) < 1e-9

def test_hybrid_operator_custom_routing_unknown_raises():
    custom = HybridOperator({'pow': EXL}, name="pow-only")
    with pytest.raises(AttributeError):
        custom.div

def test_hybrid_operator_repr():
    r = repr(BEST)
    assert "BEST" in r
    assert "EXL" in r
    assert "EML" in r

def test_hybrid_operator_info_prints(capsys):
    BEST.info()
    out = capsys.readouterr().out
    assert "BEST" in out
    assert "EXL" in out
    assert "EDL" in out
    assert "EML" in out
    assert "saves" in out  # node savings should be reported

def test_best_importable_from_top():
    from monogate import BEST, HybridOperator
    assert isinstance(BEST, HybridOperator)
    assert "pow" in BEST.ops()

def test_best_node_costs_all_less_than_eml():
    # Every BEST routing should use at most as many nodes as EML for that op
    from monogate.core import _NODE_COSTS
    for op_name, routing_op in BEST._routing.items():
        costs = _NODE_COSTS.get(op_name, {})
        eml_cost  = costs.get('EML')
        this_cost = costs.get(routing_op.name)
        if eml_cost is not None and this_cost is not None:
            assert this_cost <= eml_cost, (
                f"BEST.{op_name} routes to {routing_op.name} ({this_cost}n) "
                f"but EML is cheaper ({eml_cost}n)"
            )

def test_best_pow_cheaper_than_eml_pow():
    from monogate.core import _NODE_COSTS
    exl_cost = _NODE_COSTS['pow']['EXL']
    eml_cost = _NODE_COSTS['pow']['EML']
    assert exl_cost < eml_cost  # 3 < 15

def test_best_ln_cheaper_than_eml_ln():
    from monogate.core import _NODE_COSTS
    exl_cost = _NODE_COSTS['ln']['EXL']
    eml_cost = _NODE_COSTS['ln']['EML']
    assert exl_cost < eml_cost  # 1 < 3
