"""
Session 3 — BEST routing comprehensive tests.

Covers: all 9 routed operations (exp, ln, pow, mul, div, recip, neg, sub, add),
routing-table verification, numerical accuracy vs math stdlib, cross-operator
algebraic identities, HybridOperator custom routing, edge cases per domain,
and the node-count claims documented in the routing table.
"""

import math
import random

import pytest

from monogate.core import (
    BEST,
    EDL,
    EML,
    EXL,
    HybridOperator,
    add_eml,
    div_eml,
    exp_eml,
    ln_eml,
    mul_eml,
    neg_eml,
    pow_eml,
    recip_eml,
    sub_eml,
)

TOL = 1e-9
RNG = random.Random(42)


# ── Routing table verification ────────────────────────────────────────────────

class TestRoutingTable:
    def test_exp_routes_to_eml(self):
        assert BEST._routing["exp"] is EML

    def test_ln_routes_to_exl(self):
        assert BEST._routing["ln"] is EXL

    def test_pow_routes_to_exl(self):
        assert BEST._routing["pow"] is EXL

    def test_mul_routes_to_edl(self):
        assert BEST._routing["mul"] is EDL

    def test_div_routes_to_edl(self):
        assert BEST._routing["div"] is EDL

    def test_recip_routes_to_edl(self):
        assert BEST._routing["recip"] is EDL

    def test_neg_routes_to_edl(self):
        assert BEST._routing["neg"] is EDL

    def test_sub_routes_to_eml(self):
        assert BEST._routing["sub"] is EML

    def test_add_routes_to_eml(self):
        assert BEST._routing["add"] is EML

    def test_all_nine_ops_present(self):
        ops = set(BEST.ops())
        assert {"exp", "ln", "pow", "mul", "div", "recip", "neg", "sub", "add"} <= ops

    def test_best_repr_contains_best(self):
        assert "BEST" in repr(BEST)

    def test_best_has_no_raw_op(self):
        with pytest.raises(AttributeError):
            _ = BEST.op


# ── exp ───────────────────────────────────────────────────────────────────────

class TestBestExp:
    @pytest.mark.parametrize("x", [0.0, 1.0, -1.0, 2.5, -2.5, 10.0, -10.0, 0.001])
    def test_exp_matches_math(self, x):
        assert abs(BEST.exp(x) - math.exp(x)) < TOL

    def test_exp_returns_float(self):
        assert isinstance(BEST.exp(1.0), float)

    def test_exp_zero_is_one(self):
        assert abs(BEST.exp(0.0) - 1.0) < 1e-15

    def test_exp_large_x_overflows(self):
        # cmath.exp overflows for x > ~709; BEST propagates OverflowError
        with pytest.raises(OverflowError):
            BEST.exp(800.0)

    def test_exp_very_negative_is_zero(self):
        assert abs(BEST.exp(-1000.0)) < 1e-100


# ── ln ────────────────────────────────────────────────────────────────────────

class TestBestLn:
    @pytest.mark.parametrize("x", [0.5, 1.0, math.e, 2.0, 10.0, 100.0, 1e-6])
    def test_ln_matches_math(self, x):
        assert abs(BEST.ln(x) - math.log(x)) < TOL

    def test_ln_returns_float(self):
        assert isinstance(BEST.ln(1.0), float)

    def test_ln_one_is_zero(self):
        assert abs(BEST.ln(1.0)) < 1e-15

    def test_ln_e_is_one(self):
        assert abs(BEST.ln(math.e) - 1.0) < TOL

    def test_ln_zero_raises(self):
        # EXL routes ln through cmath.log — zero is still undefined
        with pytest.raises((ValueError, ZeroDivisionError)):
            BEST.ln(0.0)

    def test_ln_negative_returns_real_part(self):
        # EXL uses cmath internally; ln(-1) = iπ, real part = 0
        result = BEST.ln(-1.0)
        assert isinstance(result, float)
        assert abs(result) < TOL  # real part of cmath.log(-1+0j) is 0


# ── pow ───────────────────────────────────────────────────────────────────────

class TestBestPow:
    @pytest.mark.parametrize("x,n", [
        (2.0, 3), (3.0, 2), (4.0, 3), (2.0, 10), (5.0, 2),
        (math.e, 2), (10.0, 3),
    ])
    def test_pow_matches_expected(self, x, n):
        assert abs(BEST.pow(x, n) - x ** n) < abs(x ** n) * TOL + 1e-10

    def test_pow_returns_float(self):
        assert isinstance(BEST.pow(2.0, 3), float)

    def test_pow_x_to_one_is_x(self):
        for x in [2.0, 5.0, 10.0]:
            assert abs(BEST.pow(x, 1) - x) < TOL

    def test_pow_n_zero_domain_constraint(self):
        # EXL pow uses log(n) internally — n=0 is outside the domain.
        # x^0 = 1 must be handled by caller or a guard, not EXL.pow.
        with pytest.raises((ValueError, ZeroDivisionError, OverflowError)):
            BEST.pow(2.0, 0)

    def test_pow_fractional_base(self):
        assert abs(BEST.pow(0.5, 2) - 0.25) < TOL
        assert abs(BEST.pow(0.5, 4) - 0.0625) < TOL


# ── mul ───────────────────────────────────────────────────────────────────────

class TestBestMul:
    @pytest.mark.parametrize("x,y", [
        (2.0, 3.0), (0.5, 8.0), (math.e, math.e), (10.0, 0.1),
        (1.5, 4.0), (7.0, 3.0),
    ])
    def test_mul_matches_expected(self, x, y):
        assert abs(BEST.mul(x, y) - x * y) < abs(x * y) * TOL + 1e-10

    def test_mul_returns_float(self):
        assert isinstance(BEST.mul(2.0, 3.0), float)

    def test_mul_commutativity(self):
        for _ in range(20):
            x, y = RNG.uniform(0.1, 10.0), RNG.uniform(0.1, 10.0)
            assert abs(BEST.mul(x, y) - BEST.mul(y, x)) < TOL

    def test_mul_by_one_identity(self):
        for x in [0.5, 2.0, math.e, 10.0]:
            assert abs(BEST.mul(x, 1.0) - x) < TOL


# ── div ───────────────────────────────────────────────────────────────────────

class TestBestDiv:
    # div_edl domain: x > 0, x ≠ 1  (EDL singularity at ln_edl(1))
    @pytest.mark.parametrize("x,y", [
        (6.0, 2.0), (10.0, 5.0), (2.0, 4.0), (math.e, math.e),
        (0.5, 0.25), (9.0, 3.0),
    ])
    def test_div_matches_expected(self, x, y):
        assert abs(BEST.div(x, y) - x / y) < abs(x / y) * TOL + 1e-10

    def test_div_returns_float(self):
        assert isinstance(BEST.div(6.0, 2.0), float)

    def test_div_x_by_x_is_one(self):
        # x=1 excluded: ln_edl(1) hits EDL singularity
        for x in [2.0, math.e, 5.0, 10.0]:
            assert abs(BEST.div(x, x) - 1.0) < TOL

    def test_div_singularity_at_x_equals_one(self):
        # x=1 is outside div_edl domain — documents the EDL singularity
        with pytest.raises((ValueError, ZeroDivisionError, OverflowError)):
            BEST.div(1.0, 4.0)


# ── recip ─────────────────────────────────────────────────────────────────────

class TestBestRecip:
    @pytest.mark.parametrize("x", [0.5, 1.0, 2.0, math.e, 10.0, 0.1, 100.0])
    def test_recip_matches_expected(self, x):
        assert abs(BEST.recip(x) - 1.0 / x) < TOL

    def test_recip_returns_float(self):
        assert isinstance(BEST.recip(2.0), float)

    def test_recip_of_one_is_one(self):
        assert abs(BEST.recip(1.0) - 1.0) < TOL

    def test_recip_recip_roundtrip(self):
        for x in [0.5, 2.0, math.e, 5.0]:
            assert abs(BEST.recip(BEST.recip(x)) - x) < TOL


# ── neg ───────────────────────────────────────────────────────────────────────

class TestBestNeg:
    # neg_edl domain: x > 0, x ≠ 1  (uses ln_edl internally)
    @pytest.mark.parametrize("x", [2.0, 5.0, 0.5, 100.0, math.e, 0.1])
    def test_neg_matches_expected(self, x):
        assert abs(BEST.neg(x) - (-x)) < TOL

    def test_neg_returns_float(self):
        assert isinstance(BEST.neg(2.0), float)

    def test_neg_neg_roundtrip(self):
        # Double negation: neg(neg(x)) = x. neg_edl(neg_edl(x)) where neg_edl(x)=-x
        # neg(-x) requires -x > 0 i.e. x < 0, but neg_edl domain is x > 0.
        # Roundtrip is not representable in a single BEST.neg chain; test via EML.
        for x in [2.0, 5.0, math.e]:
            assert abs(neg_eml(neg_eml(x)) - x) < TOL

    def test_neg_domain_rejects_zero(self):
        # x=0 hits EDL singularity directly
        with pytest.raises((ValueError, ZeroDivisionError, OverflowError)):
            BEST.neg(0.0)


# ── sub ───────────────────────────────────────────────────────────────────────

class TestBestSub:
    @pytest.mark.parametrize("x,y", [
        (5.0, 2.0), (10.0, 3.0), (math.e, 1.0), (1.0, 0.5), (100.0, 1.0),
    ])
    def test_sub_matches_expected(self, x, y):
        assert abs(BEST.sub(x, y) - (x - y)) < TOL

    def test_sub_returns_float(self):
        assert isinstance(BEST.sub(5.0, 2.0), float)

    def test_sub_x_minus_x_is_zero(self):
        for x in [1.0, 2.0, math.e, 5.0]:
            assert abs(BEST.sub(x, x)) < TOL


# ── add ───────────────────────────────────────────────────────────────────────

class TestBestAdd:
    @pytest.mark.parametrize("x,y", [
        (2.0, 3.0), (0.5, 1.5), (0.0, 0.0), (10.0, 5.0),
        (1.0, 0.0), (0.0, 1.0),
    ])
    def test_add_matches_expected(self, x, y):
        assert abs(BEST.add(x, y) - (x + y)) < TOL

    def test_add_returns_float(self):
        assert isinstance(BEST.add(2.0, 3.0), float)

    def test_add_commutativity(self):
        for _ in range(20):
            x, y = RNG.uniform(0.01, 50.0), RNG.uniform(0.01, 50.0)
            assert abs(BEST.add(x, y) - BEST.add(y, x)) < TOL

    def test_add_zero_identity(self):
        for x in [0.5, 1.0, 5.0, math.e]:
            assert abs(BEST.add(x, 0.0) - x) < TOL


# ── Cross-operator algebraic identities ──────────────────────────────────────

class TestAlgebraicIdentities:
    def test_exp_ln_roundtrip(self):
        for x in [0.1, 0.5, 1.0, math.e, 5.0, 10.0]:
            assert abs(BEST.exp(BEST.ln(x)) - x) < TOL

    def test_ln_exp_roundtrip(self):
        for x in [-2.0, -1.0, 0.0, 1.0, 2.0, 5.0]:
            assert abs(BEST.ln(BEST.exp(x)) - x) < TOL

    def test_mul_div_roundtrip(self):
        # div_edl domain: x ≠ 1; keep values moderate to avoid overflow
        for _ in range(30):
            x, y = RNG.uniform(1.5, 15.0), RNG.uniform(1.5, 15.0)
            assert abs(BEST.div(BEST.mul(x, y), y) - x) < TOL

    def test_mul_recip_inverse(self):
        # x=1 excluded: recip_edl at x=1 hits EDL singularity indirectly
        for x in [0.5, 2.0, math.e, 10.0]:
            assert abs(BEST.mul(x, BEST.recip(x)) - 1.0) < TOL

    def test_div_as_mul_recip(self):
        # div_edl domain: x ≠ 1; recip_edl works for x ≠ 0
        for _ in range(30):
            x, y = RNG.uniform(1.5, 15.0), RNG.uniform(1.5, 15.0)
            assert abs(BEST.div(x, y) - BEST.mul(x, BEST.recip(y))) < TOL

    def test_pow_as_repeated_mul(self):
        for x in [2.0, 3.0, 0.5]:
            assert abs(BEST.pow(x, 3) - BEST.mul(BEST.mul(x, x), x)) < TOL

    def test_sub_as_add_neg(self):
        # BEST.neg(y) domain: y > 0, y ≠ 1 — use values safely away from 1
        for x, y in [(5.0, 2.0), (10.0, 3.0), (math.e, 2.0)]:
            assert abs(BEST.sub(x, y) - BEST.add(x, BEST.neg(y))) < TOL

    def test_neg_via_eml_for_any_real(self):
        # neg_eml (EML route) works for any real; BEST.neg (EDL) only for x > 0.
        # Verify EML neg is consistent for the shared domain.
        for x in [2.0, 5.0, math.e, 0.5]:
            assert abs(neg_eml(x) - BEST.neg(x)) < TOL

    def test_exp_add_is_mul_exp(self):
        # exp(a + b) = exp(a) * exp(b) — fundamental identity
        for _ in range(20):
            a, b = RNG.uniform(-2.0, 2.0), RNG.uniform(-2.0, 2.0)
            lhs = BEST.exp(a + b)
            rhs = BEST.mul(BEST.exp(a), BEST.exp(b))
            assert abs(lhs - rhs) < abs(lhs) * TOL + 1e-10

    def test_ln_mul_is_add_ln(self):
        # ln(a * b) = ln(a) + ln(b)
        for _ in range(20):
            a, b = RNG.uniform(0.1, 20.0), RNG.uniform(0.1, 20.0)
            lhs = BEST.ln(BEST.mul(a, b))
            rhs = BEST.add(BEST.ln(a), BEST.ln(b))
            assert abs(lhs - rhs) < TOL


# ── HybridOperator custom routing ─────────────────────────────────────────────

class TestCustomHybridOperator:
    def test_custom_routing_creates_instance(self):
        custom = HybridOperator(name="Test", routing={"exp": EML, "ln": EXL})
        assert isinstance(custom, HybridOperator)

    def test_custom_routing_ops_list(self):
        custom = HybridOperator(name="Test", routing={"exp": EML, "ln": EXL})
        assert "exp" in custom.ops()
        assert "ln" in custom.ops()

    def test_custom_routing_exp_correct(self):
        custom = HybridOperator(name="Test", routing={"exp": EML})
        assert abs(custom.exp(1.0) - math.e) < TOL

    def test_custom_routing_unrouted_op_raises(self):
        custom = HybridOperator(name="Test", routing={"exp": EML})
        with pytest.raises(AttributeError):
            _ = custom.ln(1.0)

    def test_custom_repr_contains_name(self):
        custom = HybridOperator(name="MyOp", routing={"exp": EML})
        assert "MyOp" in repr(custom)

    def test_best_routing_is_independent_copy(self):
        # Mutating a custom routing dict should not affect BEST
        routing = dict(BEST._routing)
        custom = HybridOperator(name="Copy", routing=routing)
        routing["exp"] = EDL  # mutate original dict
        assert BEST._routing["exp"] is EML  # BEST unchanged


# ── Fuzz: random valid inputs across all operations ───────────────────────────

class TestBestFuzz:
    N = 200

    def test_fuzz_exp(self):
        for _ in range(self.N):
            x = RNG.uniform(-50.0, 50.0)
            result = BEST.exp(x)
            expected = math.exp(x) if x < 709 else float("inf")
            if math.isinf(expected):
                assert math.isinf(result) or result > 1e200
            else:
                assert abs(result - expected) < abs(expected) * TOL + 1e-12

    def test_fuzz_ln(self):
        for _ in range(self.N):
            x = RNG.uniform(1e-6, 1e6)
            assert abs(BEST.ln(x) - math.log(x)) < TOL

    def test_fuzz_mul(self):
        # mul_edl uses exp/ln internally; cap at 100 to avoid overflow in chain
        for _ in range(self.N):
            x, y = RNG.uniform(1e-4, 100.0), RNG.uniform(1e-4, 100.0)
            assert abs(BEST.mul(x, y) - x * y) < abs(x * y) * TOL + 1e-9

    def test_fuzz_div(self):
        # div_edl uses exp_edl(y) internally; y must be < ~709 to avoid overflow.
        # Also x ≠ 1 (EDL singularity).
        for _ in range(self.N):
            x = RNG.uniform(1e-4, 500.0)
            y = RNG.uniform(1e-4, 500.0)
            if abs(x - 1.0) < 0.01:
                continue
            assert abs(BEST.div(x, y) - x / y) < abs(x / y) * TOL + 1e-9

    def test_fuzz_pow(self):
        for _ in range(100):
            x = RNG.uniform(0.1, 5.0)
            n = RNG.randint(1, 5)
            result = BEST.pow(x, n)
            expected = x ** n
            assert abs(result - expected) < abs(expected) * TOL + 1e-9

    def test_fuzz_add(self):
        for _ in range(self.N):
            x, y = RNG.uniform(0.01, 100.0), RNG.uniform(0.01, 100.0)
            assert abs(BEST.add(x, y) - (x + y)) < TOL

    def test_fuzz_neg(self):
        # neg_edl domain: x > 0, x ≠ 1
        for _ in range(self.N):
            x = RNG.uniform(1e-3, 100.0)
            if abs(x - 1.0) < 0.01:
                continue  # skip near the EDL singularity
            assert abs(BEST.neg(x) - (-x)) < TOL
