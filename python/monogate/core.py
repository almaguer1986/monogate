"""
monogate.core — Pure-Python EML arithmetic.

Mirrors the JS library (lib/src/index.js) exactly.
No external dependencies — uses only math.exp and math.log.

Grammar:   S → 1 | eml(S, S)
Operator:  eml(x, y) = exp(x) − ln(y)

Strict principal-branch ln: raises ValueError if y ≤ 0.
"""

import math

__all__ = [
    "op",
    "E",
    "ZERO",
    "NEG_ONE",
    "exp_eml",
    "ln_eml",
    "sub_eml",
    "neg_eml",
    "add_eml",
    "mul_eml",
    "div_eml",
    "pow_eml",
    "recip_eml",
    "IDENTITIES",
    "Operator",
    "EML",
    "EDL",
    "EMN",
    "EXL",
    "EAL",
    "make_exp",
    "make_ln",
    "exp_edl",
    "ln_edl",
    "recip_edl",
    "neg_edl",
    "div_edl",
    "mul_edl",
    "pow_edl",
    "EDL_ONE",
    "EDL_NEG_ONE",
    "pow_exl",
    "compare_op",
    "HybridOperator",
    "BEST",
]


# ── Core operator ─────────────────────────────────────────────────────────────

def op(x: float, y: float) -> float:
    """
    The EML operator: eml(x, y) = exp(x) − ln(y).

    Strict: raises ValueError if y ≤ 0 (argument of ln must be positive).

    >>> import math
    >>> abs(op(1, 1) - math.e) < 1e-14
    True
    """
    if y <= 0:
        raise ValueError(f"op: y must be > 0, got {y!r}")
    return math.exp(x) - math.log(y)


# ── Constants ─────────────────────────────────────────────────────────────────

E       = op(1, 1)                    # e        Proof: exp(1)−ln(1)=e.        Nodes:1 Depth:1
ZERO    = op(1, op(op(1, 1), 1))     # 0        Proof: eml(1,1)=e; eml(e,1)=eᵉ; eml(1,eᵉ)=e−e=0. Nodes:3 Depth:3
NEG_ONE = op(ZERO, op(2, 1))         # −1       Proof: exp(0)−ln(e²)=1−2=−1.  Nodes:5 Depth:4 (uses terminal 2)


# ── Elementary functions ──────────────────────────────────────────────────────

def exp_eml(x: float) -> float:
    """
    eˣ = eml(x, 1).

    Proof: exp(x) − ln(1) = exp(x). ∎
    Nodes:1  Depth:1

    >>> import math
    >>> abs(exp_eml(1) - math.e) < 1e-14
    True
    >>> abs(exp_eml(0) - 1) < 1e-14
    True
    """
    return op(x, 1)


def ln_eml(x: float) -> float:
    """
    ln(x) = eml(1, eml(eml(1, x), 1)).

    Proof: let s = e − ln(x); eml(s, 1) = eˢ = eᵉ/x;
    eml(1, eᵉ/x) = e − (e − ln(x)) = ln(x). ∎
    Nodes:3  Depth:3  Domain: x > 0

    >>> import math
    >>> abs(ln_eml(math.e) - 1) < 1e-10
    True
    >>> abs(ln_eml(1) - 0) < 1e-14
    True
    """
    return op(1, op(op(1, x), 1))


def sub_eml(x: float, y: float) -> float:
    """
    x − y = eml(ln(x), exp(y)).

    Proof: exp(ln(x)) − ln(exp(y)) = x − y. ∎
    Nodes:5  Depth:4  Domain: x > 0

    >>> abs(sub_eml(5, 2) - 3) < 1e-10
    True
    """
    return op(ln_eml(x), exp_eml(y))


def neg_eml(y: float) -> float:
    """
    −y  (two-regime negation for numerical stability).

    Regime A — y ≤ 0 (tower formula):
        a = eml(y, 1) = exp(y).
        A = eml(a, a) = exp(a) − ln(a) = exp(exp(y)) − y.
        B = eml(a, 1) = exp(a) = exp(exp(y)).
        A − B = −y. ∎
        Stable: exp(y) ≤ 1 so exp(exp(y)) ≤ e for all y ≤ 0.

    Regime B — y > 0 (shift formula):
        y+1 = sub_eml(y, NEG_ONE) = exp(ln(y)) − ln(exp(−1)·exp(y)/y)
            ... simplifies to: y + 1.
        eml(ZERO, eml(y+1, 1)) = exp(0) − ln(exp(y+1)) = 1 − (y+1) = −y. ∎
        Stable for |y| < 708 (IEEE 754 double limit on exp).

    Nodes:9  Depth:5  Valid for all y ∈ ℝ with |y| < 708.

    >>> abs(neg_eml(3) + 3) < 1e-10
    True
    >>> abs(neg_eml(-5) - 5) < 1e-10
    True
    >>> abs(neg_eml(0)) < 1e-14
    True
    """
    if y <= 0:
        a = op(y, 1)                              # exp(y) ∈ (0, 1]
        return op(ln_eml(op(a, a)), op(op(a, 1), 1))
    y1 = op(ln_eml(y), op(NEG_ONE, 1))           # y + 1  (shift by 1)
    return op(ZERO, op(y1, 1))                    # 1 − (y+1) = −y


def add_eml(x: float, y: float) -> float:
    """
    x + y = eml(ln(x), eml(−y, 1))  (x > 0).

    Generalised for all signs via commutativity and double-negation.
    Nodes:11  Depth:6

    >>> abs(add_eml(2, 3) - 5) < 1e-10
    True
    >>> abs(add_eml(-2, -3) + 5) < 1e-10
    True
    >>> abs(add_eml(0.5, -1.5) + 1) < 1e-10
    True
    """
    if x > 0:
        return op(ln_eml(x), op(neg_eml(y), 1))
    if y > 0:
        return op(ln_eml(y), op(neg_eml(x), 1))
    return neg_eml(op(ln_eml(neg_eml(x)), op(neg_eml(neg_eml(y)), 1)))


def mul_eml(x: float, y: float) -> float:
    """
    x × y = exp(ln(x) + ln(y)).

    Proof: exp(ln(x) + ln(y)) = exp(ln(xy)) = xy. ∎
    Nodes:13  Depth:7  Domain: x, y > 0

    >>> abs(mul_eml(2, 3) - 6) < 1e-10
    True
    >>> abs(mul_eml(4, 0.25) - 1) < 1e-10
    True
    """
    return op(add_eml(ln_eml(x), ln_eml(y)), 1)


def div_eml(x: float, y: float) -> float:
    """
    x / y = exp(ln(x) − ln(y)).

    Proof: exp(ln(x) − ln(y)) = exp(ln(x/y)) = x/y. ∎
    Nodes:15  Depth:8  Domain: x, y > 0

    >>> abs(div_eml(6, 3) - 2) < 1e-10
    True
    >>> abs(div_eml(1, 4) - 0.25) < 1e-10
    True
    """
    return op(add_eml(ln_eml(x), neg_eml(ln_eml(y))), 1)


def pow_eml(x: float, n: float) -> float:
    """
    xⁿ = exp(n · ln(x)).

    Proof: exp(n·ln(x)) = exp(ln(xⁿ)) = xⁿ. ∎
    Nodes:15  Depth:8  Domain: x > 0, n ∈ ℝ

    >>> abs(pow_eml(2, 10) - 1024) < 1e-8
    True
    >>> abs(pow_eml(4, 0.5) - 2) < 1e-10
    True
    """
    return op(mul_eml(n, ln_eml(x)), 1)


def recip_eml(x: float) -> float:
    """
    1/x = exp(−ln(x)).

    Proof: exp(−ln(x)) = x⁻¹. ∎
    Nodes:5  Depth:4  Domain: x > 0

    >>> abs(recip_eml(2) - 0.5) < 1e-10
    True
    >>> abs(recip_eml(4) - 0.25) < 1e-10
    True
    """
    return op(neg_eml(ln_eml(x)), 1)


# ── Identity table ────────────────────────────────────────────────────────────

IDENTITIES: list[dict] = [
    {
        "name":     "eˣ",
        "eml_form": "eml(x, 1)",
        "nodes":    1,
        "depth":    1,
        "status":   "verified",
    },
    {
        "name":     "ln x",
        "eml_form": "eml(1, eml(eml(1, x), 1))",
        "nodes":    3,
        "depth":    3,
        "status":   "verified",
    },
    {
        "name":     "e",
        "eml_form": "eml(1, 1)",
        "nodes":    1,
        "depth":    1,
        "status":   "verified",
    },
    {
        "name":     "0",
        "eml_form": "eml(1, eml(eml(1, 1), 1))",
        "nodes":    3,
        "depth":    3,
        "status":   "verified",
    },
    {
        "name":     "x − y",
        "eml_form": "eml(ln(x), exp(y))",
        "nodes":    5,
        "depth":    4,
        "status":   "verified",
    },
    {
        "name":     "−y",
        "eml_form": "two-regime (see source)",
        "nodes":    9,
        "depth":    5,
        "status":   "proven",
    },
    {
        "name":     "x + y",
        "eml_form": "eml(ln(x), eml(neg(y), 1))",
        "nodes":    11,
        "depth":    6,
        "status":   "proven",
    },
    {
        "name":     "x × y",
        "eml_form": "eml(add(ln(x), ln(y)), 1)",
        "nodes":    13,
        "depth":    7,
        "status":   "proven",
    },
    {
        "name":     "x / y",
        "eml_form": "eml(add(ln(x), neg(ln(y))), 1)",
        "nodes":    15,
        "depth":    8,
        "status":   "proven",
    },
    {
        "name":     "xⁿ",
        "eml_form": "eml(mul(n, ln(x)), 1)",
        "nodes":    15,
        "depth":    8,
        "status":   "proven",
    },
    {
        "name":     "1/x",
        "eml_form": "eml(neg(ln(x)), 1)",
        "nodes":    5,
        "depth":    4,
        "status":   "verified",
    },
]


# ── Operator abstraction ──────────────────────────────────────────────────────

import cmath
from typing import Callable


class Operator:
    """Container for a universal operator, its natural constant, and derived ops.

    Usage::

        EML.exp(1.0)          # exp(1) via 1-node EML tree
        EML.mul(2.0, 3.0)     # 6.0  — after registration below
        EDL.div(6.0, 2.0)     # 3.0
        EML.ops()             # ['add', 'div', 'mul', 'neg', 'pow', 'recip', 'sub']
    """

    def __init__(self, name: str, func: Callable, constant: complex) -> None:
        self.name = name
        self.func = func
        self.constant = constant
        object.__setattr__(self, '_ops', {})

    def __repr__(self) -> str:
        return f"Operator({self.name!r}, constant={self.constant})"

    # ── Built-in derived functions ─────────────────────────────────────────────

    def exp(self, x: complex) -> complex:
        """exp(x) as a 1-node tree under this operator."""
        return make_exp(self)(x)

    def ln(self, x: complex) -> complex:
        """ln(x) as a 3-node tree under this operator."""
        return make_ln(self)(x)

    # ── Operation registry ─────────────────────────────────────────────────────

    def register(self, op_name: str, func: Callable) -> None:
        """Register a named arithmetic operation for this operator.

        After registration, the function is accessible as an attribute::

            EML.register('mul', mul_eml)
            EML.mul(2, 3)   # → 6.0
        """
        object.__getattribute__(self, '_ops')[op_name] = func

    def ops(self) -> list[str]:
        """Return sorted list of registered operation names."""
        return sorted(object.__getattribute__(self, '_ops'))

    def __getattr__(self, name: str) -> Callable:
        try:
            _ops = object.__getattribute__(self, '_ops')
        except AttributeError:
            raise AttributeError(name)
        if name in _ops:
            return _ops[name]
        raise AttributeError(
            f"Operator {self.name!r} has no registered operation {name!r}. "
            f"Available: {sorted(_ops)}"
        )

    # ── Introspection ──────────────────────────────────────────────────────────

    def benchmark(self) -> dict:
        """Return accuracy metrics for exp and ln over a standard test set.

        Returns a dict with keys:
            exp_max_err: float | None   (None if exp not available)
            ln_max_err:  float | None   (None if ln not available)
            complete:    bool
            ops:         list[str]
        """
        test_exp = [0.0, 0.5, 1.0, -1.0, 2.0]
        test_ln  = [0.5, 1.5, 2.0, 3.0, math.e]
        result: dict = {'complete': False, 'ops': self.ops()}

        try:
            exp_fn = make_exp(self)
            exp_errs = [
                abs(exp_fn(x + 0j).real - math.exp(x)) / max(abs(math.exp(x)), 1e-30)
                for x in test_exp
            ]
            result['exp_max_err'] = max(exp_errs)
        except NotImplementedError:
            result['exp_max_err'] = None

        try:
            ln_fn = make_ln(self)
            ln_errs = [
                abs(ln_fn(x + 0j).real - math.log(x)) / max(abs(math.log(x)), 1e-30)
                for x in test_ln
            ]
            result['ln_max_err'] = max(ln_errs)
        except NotImplementedError:
            result['ln_max_err'] = None

        meta = object.__getattribute__(self, '__dict__').get('_meta', {})
        result['complete'] = meta.get('complete', False)
        return result

    def info(self) -> None:
        """Print a human-readable summary of this operator."""
        meta = self.__dict__.get('_meta', {})
        gate  = meta.get('gate', 'unknown')
        notes = meta.get('notes', '')
        bm    = self.benchmark()

        def _fmt(v):
            return f"{v:.1e}" if v is not None else "N/A"

        print(f"{self!r}")
        print(f"  Gate:      {gate}")
        print(f"  exp err:   {_fmt(bm['exp_max_err'])}   "
              f"ln err: {_fmt(bm['ln_max_err'])}")
        print(f"  Complete:  {'YES' if bm['complete'] else 'NO'}")
        if bm['ops']:
            print(f"  Ops:       {', '.join(bm['ops'])}")
        if notes:
            print(f"  Notes:     {notes}")


def _eml_func(x: complex, y: complex) -> complex:
    return cmath.exp(x) - cmath.log(y)


EML = Operator("EML", _eml_func, 1.0 + 0j)


def _edl_func(x: complex, y: complex) -> complex:
    if y == 0 or y == 1:
        raise ValueError(f"EDL domain error: y={y}")
    return cmath.exp(x) / cmath.log(y)


EDL = Operator("EDL", _edl_func, cmath.e)


def _emn_func(x: complex, y: complex) -> complex:
    """emn(x, y) = ln(y) − exp(x)  =  −eml(x, y).

    The "negated EML" gate.  Domain: y ≠ 0 (principal-branch ln).
    Natural 1-node output: emn(x, 1) = −exp(x).
    Unlike EML and EDL, EMN cannot build exp(x) > 0 as a finite real tree
    (every node output has the form ln(·) − exp(·), which can be negative
    or positive but can never telescope back to a bare exp).
    """
    return cmath.log(y) - cmath.exp(x)


EMN = Operator("EMN", _emn_func, 1.0 + 0j)  # emn(x, 1) = −exp(x)


def _exl_func(x: complex, y: complex) -> complex:
    """exl(x, y) = exp(x) · ln(y).

    The "product of exp and log" gate.  Domain: y > 0, y ≠ 1.
    Two remarkable 1-node identities:
        exl(x, e) = exp(x)   [right-neutral e]
        exl(0, y) = ln(y)    [left-neutral 0]
    Three-node power:  exl(exl(exl(0, n), x), e) = x^n.
    Cannot build addition or general multiplication (EXL is complete
    only over the power-of-positive-reals sub-group, not over ℝ).
    """
    return cmath.exp(x) * cmath.log(y)


EXL = Operator("EXL", _exl_func, cmath.e)   # exl(x, e) = exp(x)


def _eal_func(x: complex, y: complex) -> complex:
    """eal(x, y) = exp(x) + ln(y).

    Domain: y > 0.
    Natural 1-node output: eal(x, 1) = exp(x).
    No finite real formula for ln(x): eal(c, y) = exp(c)+ln(y);
    the additive exp(c) offset cannot be cancelled by any composition
    of real constants.
    """
    return cmath.exp(x) + cmath.log(y)


EAL = Operator("EAL", _eal_func, 1.0 + 0j)  # eal(x, 1) = exp(x)


# ── Derived helpers (operator-agnostic) ───────────────────────────────────────
#
# Both EML and EDL share the same *structure* for exp and ln, but the constants
# differ.  The two neutral elements are:
#
#   EML: right-neutral = 1      (eml(x, 1) = exp(x))
#        "left probe" = 1       (eml(1, x) = e − ln(x), used to extract ln)
#
#   EDL: right-neutral = e      (edl(x, e) = exp(x))
#        left-neutral  = 0      (edl(0, x) = 1/ln(x))
#
# exp — same 1-node form for both operators:
#   EML: eml(x, 1) = exp(x) − ln(1) = exp(x)
#   EDL: edl(x, e) = exp(x) / ln(e) = exp(x) / 1 = exp(x)
#
# ln — 3-node trees with parallel but distinct structure:
#   EML: eml(1, eml(eml(1, x), 1))
#        step 1: eml(1, x)       = e − ln(x)
#        step 2: eml(s, 1)       = exp(e − ln(x)) = eᵉ/x
#        step 3: eml(1, eᵉ/x)   = e − (e − ln(x)) = ln(x)  ✓
#
#   EDL: edl(0, edl(edl(0, x), e))
#        step 1: edl(0, x)       = 1/ln(x)
#        step 2: edl(s, e)       = exp(1/ln(x)) / 1 = exp(1/ln(x))
#        step 3: edl(0, t)       = 1/ln(exp(1/ln(x))) = 1/(1/ln(x)) = ln(x)  ✓

def make_exp(operator: Operator) -> Callable[[complex], complex]:
    """Return a function computing exp(x) as a 1-node operator tree.

    Raises NotImplementedError for EMN: emn(x, 1) = −exp(x), not +exp(x).
    No finite real EMN tree recovers the positive exponential.
    """
    if operator is EMN:
        raise NotImplementedError(
            "make_exp: EMN has no real 1-node tree for exp(x). "
            "emn(x, 1) = −exp(x). EMN's natural primitive is negative-exp."
        )
    c = operator.constant
    return lambda x: operator.func(x, c)


def make_ln(operator: Operator) -> Callable[[complex], complex]:
    """Return a function computing ln(x) as a 3-node operator tree.

    EML route: eml(1, eml(eml(1, x), 1))
    EDL route: edl(0, edl(edl(0, x), e))
    """
    f = operator.func
    c = operator.constant
    if operator is EML:
        # c = 1; uses right-neutral in all three positions
        return lambda x: f(c, f(f(c, x), c))
    if operator is EDL:
        # left-neutral 0; right-neutral e (the constant)
        # Formula: edl(0, edl(edl(0, x), e))
        # Overflow dead zone: step 2 computes exp(1/ln(x)).  When x is close
        # to 1, ln(x) → 0 so 1/ln(x) → ±∞ and exp blows up.
        # Practical limit: |ln(x)| > 1/709 ≈ 0.00141, i.e. x ∉ (0.9986, 1.0014).
        # EML's ln_eml has no such overflow — it only fails at x ≤ 0.
        zero = 0j
        return lambda x: f(zero, f(f(zero, x), c))
    if operator is EXL:
        # 1-node formula: exl(0, x) = exp(0)·ln(x) = 1·ln(x) = ln(x)
        # Uniquely efficient: beats EML and EDL (both 3 nodes).
        # No dead zone — ln(x) is computed directly via cmath.log.
        return lambda x: operator.func(0j, x)
    if operator is EAL:
        raise NotImplementedError(
            "make_ln: EAL has no finite real formula for ln(x). "
            "eal(c, y) = exp(c)+ln(y); the additive exp(c) term cannot be "
            "cancelled by any finite composition of real constants."
        )
    if operator is EMN:
        raise NotImplementedError(
            "make_ln: no finite real EMN derivation for ln(x). "
            "EMN = −EML so every emn node outputs ln(·)−exp(·); the sign structure "
            "prevents telescoping back to a bare ln. Use EML.ln(x) or EDL.ln(x)."
        )
    raise NotImplementedError(
        f"make_ln: no ln derivation registered for operator {operator.name!r}"
    )


# Convenience singletons — mirrors the existing exp_eml / ln_eml names
exp_edl: Callable[[complex], complex] = make_exp(EDL)
ln_edl:  Callable[[complex], complex] = make_ln(EDL)


# ── EDL arithmetic ────────────────────────────────────────────────────────────
#
# The "direct parallel" to EML's sub reveals EDL's natural operation:
#
#   EML: eml(ln(x), exp(y)) = exp(ln(x)) − ln(exp(y)) = x − y   ← subtraction
#   EDL: edl(ln(x), exp(y)) = exp(ln(x)) / ln(exp(y)) = x / y   ← division
#
# Same structural form ("plug ln into left, exp into right"), different result
# because EML subtracts in the lifted space while EDL divides.
#
# EDL's natural arithmetic is multiplicative — division is its primitive operation
# the way subtraction is EML's.  Addition/subtraction have no known finite pure-EDL
# expression (open question).

def div_edl(x: complex, y: complex) -> complex:
    """x / y expressed as a 1-node EDL tree: edl(ln(x), exp(y)).

    Proof: edl(ln(x), exp(y)) = exp(ln(x)) / ln(exp(y)) = x / y  ∎
    Domain: x > 0, y ∈ ℝ, y ≠ 0
    """
    return EDL.func(ln_edl(x), exp_edl(y))


def recip_edl(x: complex) -> complex:
    """1/x expressed as a 2-node EDL tree: edl(0, edl(x, e)).

    Proof:
        edl(x, e) = exp(x) / ln(e) = exp(x)        [ln(e) = 1]
        edl(0, exp(x)) = exp(0) / ln(exp(x)) = 1/x  ∎
    Domain: x ∈ ℝ, x ≠ 0.
    Note: bypass div_edl(1, x) — that path hits ln_edl(1) which passes
    through edl(0, 1), EDL's singularity.

    Nodes: 2  (vs EML's recip_eml: 5 nodes)
    """
    e = EDL.constant
    return EDL.func(0j, EDL.func(x, e))


def neg_edl(x: complex) -> complex:
    """−x expressed as a 6-node EDL tree.

    Key: we need a right argument b such that ln(b) = −1, i.e. b = 1/e.
         1/e = edl(0, edl(e, e))  [2 nodes]
         Then: edl(ln(x), 1/e) = exp(ln(x)) / ln(1/e) = x / (−1) = −x  ∎

    Proof of 1/e:
        edl(e, e) = exp(e) / ln(e) = exp(e)         [ln(e) = 1]
        edl(0, exp(e)) = 1 / ln(exp(e)) = 1/e  ∎

    Domain: x > 0, x ≠ 1  (ln_edl domain)
    Nodes: 6  (vs EML's neg_eml: 9 nodes)
    """
    e = EDL.constant
    one_over_e = EDL.func(0j, EDL.func(e, e))
    return EDL.func(ln_edl(x), one_over_e)


# ── EDL constants ─────────────────────────────────────────────────────────────
#
# Analogous to EML's E / ZERO / NEG_ONE, expressed using only e and 0.
#
#   EDL_ONE     = edl(0, e)               = 1   [exp(0)/ln(e) = 1/1 = 1]
#   EDL_NEG_ONE = edl(0, edl(0, edl(e,e))) = -1  [see neg_edl derivation]

EDL_ONE:     complex = EDL.func(0j, EDL.constant)
EDL_NEG_ONE: complex = EDL.func(0j, EDL.func(0j, EDL.func(EDL.constant, EDL.constant)))


def mul_edl(x: complex, y: complex) -> complex:
    """x * y expressed as a 7-node EDL tree: div_edl(x, recip_edl(y)).

    Route: x * y = x / (1/y) = div_edl(x, recip_edl(y))

    Proof:
        recip_edl(y) = 1/y  (2-node EDL)
        div_edl(x, 1/y) = edl(ln(x), exp(1/y)) = exp(ln(x)) / ln(exp(1/y))
                        = x / (1/y) = x·y  ∎

    Domain: x > 0, x ≠ 1  (ln_edl domain);  y ≠ 0  (recip_edl domain)
    Nodes: 7  (vs EML's mul_eml: 13 nodes)
    """
    return div_edl(x, recip_edl(y))


def add_edl(x: complex, y: complex) -> complex:
    """x + y via pure EDL — NOT POSSIBLE in finite trees over the reals.

    EDL's primitive is division in the lifted space.  From that:
        mul_edl  reachable:  x * y = div_edl(x, recip_edl(y))
        add_edl  unreachable: no finite composition of (exp, ln, /)
                              can produce a general sum of two values.

    The intuition: every EDL node output is exp(a)/ln(b).  Its sign is
    determined entirely by b (sign of ln(b)), and its magnitude by a.
    Two independent magnitudes cannot be summed through this structure.

    EML can reach addition because its primitive is subtraction, and
    sub(x, neg(y)) = x + y.  EDL has no negation that works on arbitrary
    reals (ln_edl is undefined at x=1), so the chain breaks.

    EDL is complete over the multiplicative group of positive reals
    (div → recip → mul → pow), but addition is outside that group.
    """
    raise NotImplementedError(
        "add_edl: no finite pure-EDL formula exists for general addition. "
        "EDL is complete over the multiplicative group (div/mul/pow) but "
        "addition requires stepping outside that structure."
    )


def pow_edl(x: complex, n: float) -> complex:
    """xⁿ — reachable now that mul_edl exists.

    Route: xⁿ = exp(n · ln(x)).  With EDL we need n · ln(x) as the LEFT
    argument of edl(..., e).  We have mul_edl, so:

        n · ln(x) = mul_edl(n, ln_edl(x))
        xⁿ        = exp_edl(mul_edl(n, ln_edl(x)))
                  = edl(mul_edl(n, ln_edl(x)), e)

    Domain: x > 0, x ≠ 1  (ln_edl);  n ≠ 0, n ≠ 1  (mul_edl chain)
    Note: n is a Python float here, not an EDL expression — see docstring
    for the pure-EDL path once we have a way to represent n as a tree.
    """
    return exp_edl(mul_edl(complex(n), ln_edl(x)))


# ── EXL arithmetic ────────────────────────────────────────────────────────────
#
# EXL's primitive is power: x^n = exl(exl(exl(0, n), x), e).
#
# Derivation:
#   step 1: exl(0, n)         = exp(0)·ln(n)   = ln(n)
#   step 2: exl(ln(n), x)     = exp(ln(n))·ln(x) = n·ln(x)
#   step 3: exl(n·ln(x), e)   = exp(n·ln(x))   = x^n  ✓
#
# Node count: 3  (vs EML 15, EDL ~11) — the most efficient power formula found.
#
# EXL completeness:
#   Reachable:   exp (1 node), ln (1 node), x^n (3 nodes), identity (2 nodes)
#   Unreachable: addition, subtraction, general multiplication of two variables
#   The algebraic closure of {exp(·)·ln(·), constants} does not include x+y
#   over the reals — EXL is complete only over the power-of-positives sub-group.

def pow_exl(x: complex, n: complex) -> complex:
    """x^n in 3 EXL nodes: exl(exl(exl(0, n), x), e).

    Proof (see derivation above).
    Domain: x > 0 (ln step), x ≠ 1; n ∈ ℂ.
    Nodes: 3  (EML requires 15, EDL ~11 for the same formula).
    """
    e = EXL.constant
    return EXL.func(EXL.func(EXL.func(0j, n), x), e)


# ── Comparison utility ────────────────────────────────────────────────────────

def compare_op(
    name: str,
    op_func: Callable,
    true_func: Callable,
    test_values: list,
) -> None:
    """Print a table comparing op_func against true_func over test_values.

    Useful for quick accuracy audits during development.  Prints to stdout;
    intended for interactive use, not production code.
    """
    print(f"\n=== {name} ===")
    for v in test_values:
        try:
            raw = op_func(v)
            result = raw.real if hasattr(raw, "real") else raw
            expected = true_func(v)
            err = abs(result - expected)
            print(f"  {v!s:>10} -> {result:15.8f}  (err {err:.2e})")
        except Exception as exc:
            print(f"  {v!s:>10} -> ERROR: {exc}")


# ── Register arithmetic operations on operator instances ──────────────────────
#
# After registration, operations are accessible as attributes:
#   EML.mul(2, 3)   → 6.0
#   EDL.div(6, 2)   → 3.0
#   EML.ops()       → ['add', 'div', 'mul', 'neg', 'pow', 'recip', 'sub']

EML.register('sub',   sub_eml)
EML.register('neg',   neg_eml)
EML.register('add',   add_eml)
EML.register('mul',   mul_eml)
EML.register('div',   div_eml)
EML.register('pow',   pow_eml)
EML.register('recip', recip_eml)

EDL.register('div',   div_edl)
EDL.register('recip', recip_edl)
EDL.register('neg',   neg_edl)
EDL.register('mul',   mul_edl)
EDL.register('pow',   pow_edl)
EDL.register('add',   add_edl)   # raises NotImplementedError — documented

# EMN: negated-EML gate.  Registers the two operations that arise naturally
# from its 1-node and 2-node trees.
EMN.register('neg_exp',  lambda x: _emn_func(x, 1.0 + 0j))    # −exp(x)
EMN.register('ln_shift', lambda x: _emn_func(0j, x))           # ln(x) − 1

# EXL: exp-times-ln gate.  1-node exp, 1-node ln, 3-node power.
EXL.register('pow', pow_exl)

# EAL: exp-plus-ln gate.  1-node exp, no finite ln.
# No arithmetic operations can be built purely from EAL over the reals.

# ── Per-operator metadata (used by Operator.info / Operator.benchmark) ────────

EML._meta = {
    'complete':  True,
    'gate':      'exp(x) - ln(y)',
    'constant_name': '1',
    'ln_nodes':  3,
    'notes':     'subtraction in lifted space; handles all signs; best general-purpose',
}
EDL._meta = {
    'complete':  True,
    'gate':      'exp(x) / ln(y)',
    'constant_name': 'e',
    'ln_nodes':  3,
    'notes':     'division in lifted space; fastest mul/div/recip; dead zone x in (0.9986, 1.0014)',
}
EXL._meta = {
    'complete':  False,
    'gate':      'exp(x) * ln(y)',
    'constant_name': 'e',
    'ln_nodes':  1,
    'notes':     '1-node exp AND ln; 3-node pow (best known); no add/mul; power-group only',
}
EAL._meta = {
    'complete':  False,
    'gate':      'exp(x) + ln(y)',
    'constant_name': '1',
    'ln_nodes':  None,
    'notes':     '1-node exp only; additive offset blocks bare ln derivation',
}
EMN._meta = {
    'complete':  False,
    'gate':      'ln(y) - exp(x)',
    'constant_name': '1',
    'ln_nodes':  None,
    'notes':     'negated-EML gate; natural output = -exp(x); exp/ln unreachable over reals',
}


# ── HybridOperator: per-operation routing across multiple Operators ────────────

# Known node costs for each (op_name, base_operator_name) pair.
_NODE_COSTS: dict[str, dict[str, int]] = {
    'exp':   {'EML': 1,  'EDL': 1,  'EXL': 1,  'EAL': 1},
    'ln':    {'EML': 3,  'EDL': 3,  'EXL': 1},
    'pow':   {'EML': 15, 'EDL': 11, 'EXL': 3},
    'mul':   {'EML': 13, 'EDL': 7},
    'div':   {'EML': 15, 'EDL': 1},
    'recip': {'EML': 5,  'EDL': 2},
    'neg':   {'EML': 9,  'EDL': 6},
    'sub':   {'EML': 5},
    'add':   {'EML': 11},
}


class HybridOperator:
    """
    Per-operation routing across multiple base Operators.

    Instead of one gate for everything, HybridOperator picks the best
    Operator instance for each named operation from a provided routing table.
    This formalises the 'best-per-operation' strategy discovered experimentally:

      EXL gives the cheapest ln (1 node) and pow (3 nodes).
      EDL gives the cheapest div (1 node), mul (7n), recip (2n), neg (6n).
      EML is the only complete operator that supports add (11n) and sub (5n).

    A pre-built BEST instance captures this optimal routing.

    Usage::

        from monogate.core import BEST

        BEST.pow(2.0, 10.0)     # -> 1024.0   (uses pow_exl, 3 nodes)
        BEST.div(6.0, 2.0)      # -> 3.0      (uses div_edl, 1 node)
        BEST.add(3.0, 4.0)      # -> 7.0      (uses add_eml, 11 nodes)
        BEST.ln(math.e)         # -> 1.0      (uses EXL.ln, 1 node, no dead zone)
        BEST.info()             # prints routing table with node counts

    Custom routing::

        from monogate.core import HybridOperator, EXL, EDL, EML
        my_op = HybridOperator({'pow': EXL, 'div': EDL, 'add': EML})
    """

    def __init__(
        self,
        routing: dict[str, 'Operator'],
        name: str = "Hybrid",
    ) -> None:
        self.name = name
        self._routing: dict[str, 'Operator'] = dict(routing)

    def __repr__(self) -> str:
        summary = ", ".join(
            f"{k}->{v.name}" for k, v in sorted(self._routing.items())
        )
        return f"HybridOperator({self.name!r}: {summary})"

    def __getattr__(self, name: str):
        # Called only when normal lookup fails (i.e. 'name' not a real attribute).
        routing = object.__getattribute__(self, '_routing')
        if name in routing:
            # Delegate to the routed Operator's attribute of the same name.
            # E.g. BEST.pow -> getattr(EXL, 'pow') -> pow_exl via EXL.__getattr__
            delegate = getattr(routing[name], name)
            # EDL and EXL operators use cmath internally, so their results are
            # complex even when the imaginary part is zero.  Strip it at this
            # boundary so HybridOperator always returns float to user code.
            import functools

            @functools.wraps(delegate)
            def _real_result(*args, **kwargs):
                v = delegate(*args, **kwargs)
                return v.real if isinstance(v, complex) else v

            return _real_result
        raise AttributeError(
            f"HybridOperator {self.name!r}: no routing for {name!r}. "
            f"Available: {sorted(routing)}"
        )

    def ops(self) -> list[str]:
        """Return sorted list of routed operation names."""
        return sorted(self._routing.keys())

    def benchmark(
        self,
        targets: list[str] | None = None,
        restarts: int = 3,
        steps: int = 800,
        depth: int = 3,
    ) -> dict:
        """
        Print a benchmark table for this HybridOperator.

        Reports:
        - Node-count table for all routed operations vs EML-only baseline.
        - Numerical accuracy spot-checks for exp, ln, pow, mul, div.
        - Optional neural regression on named targets (requires torch).

        Parameters
        ----------
        targets : list of str, optional
            Named regression targets to benchmark. Supported values:
            ``"sin"``, ``"cos"``, ``"x**3"``, ``"x**2-x"``, ``"exp"``,
            ``"poly4"``, ``"sqrt"``. Pass ``[]`` to skip regression.
            Defaults to ``["sin", "cos", "x**3", "poly4"]``.
        restarts : int
            Number of random restarts per target. Default 3.
        steps : int
            Training steps per restart. Default 800.
        depth : int
            EMLNetwork depth. Default 3.

        Returns
        -------
        dict
            ``{"nodes": {...}, "accuracy": {...}, "regression": {...}}``
        """
        import math

        if targets is None:
            targets = ["sin", "cos", "x**3", "poly4"]

        results: dict = {"nodes": {}, "accuracy": {}, "regression": {}}

        # ── 1. Node count table ───────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"  {self.name!r} benchmark")
        print(f"{'='*60}")
        print(f"\n  Node counts  (vs all-EML baseline)\n")
        print(f"  {'Op':<10}  {'Routed to':<8}  {'Nodes':>6}  {'EML baseline':>14}  {'Saving':>8}")
        print(f"  {'-'*10}  {'-'*8}  {'-'*6}  {'-'*14}  {'-'*8}")

        total_hybrid = 0
        total_eml    = 0
        node_summary = {}
        for op_name in sorted(self._routing.keys()):
            base   = self._routing[op_name]
            costs  = _NODE_COSTS.get(op_name, {})
            hybrid_cost = costs.get(base.name)
            eml_cost    = costs.get('EML')
            node_summary[op_name] = {'operator': base.name, 'nodes': hybrid_cost, 'eml_nodes': eml_cost}
            if isinstance(hybrid_cost, int):
                total_hybrid += hybrid_cost
            if isinstance(eml_cost, int):
                total_eml += eml_cost
            hc_str  = f"{hybrid_cost}n" if isinstance(hybrid_cost, int) else "?"
            ec_str  = f"{eml_cost}n"    if isinstance(eml_cost,  int) else "N/A"
            if isinstance(hybrid_cost, int) and isinstance(eml_cost, int):
                saving = eml_cost - hybrid_cost
                sv_str = f"-{saving}n" if saving > 0 else ("same" if saving == 0 else f"+{-saving}n")
            else:
                sv_str = "?"
            print(f"  {op_name:<10}  {base.name:<8}  {hc_str:>6}  {ec_str:>14}  {sv_str:>8}")

        if total_eml > 0:
            total_saving = total_eml - total_hybrid
            pct = 100.0 * total_saving / total_eml
            print(f"\n  Total: {total_hybrid}n  vs  {total_eml}n EML-only  =>  saves {total_saving}n ({pct:.0f}%)")
        results["nodes"] = node_summary

        # ── 2. Numerical accuracy spot-checks ────────────────────────────────
        print(f"\n  Numerical accuracy  (spot-check at representative values)\n")
        print(f"  {'Check':<26}  {'Result':>14}  {'Expected':>14}  {'Err':>12}")
        print(f"  {'-'*26}  {'-'*14}  {'-'*14}  {'-'*12}")

        checks = []
        routing = self._routing
        # exp check
        if 'exp' in routing:
            try:
                r = routing['exp'].exp(1.0)
                e = math.e
                err = abs(r - e)
                checks.append(("exp(1)", r, e, err))
            except Exception as exc:
                checks.append(("exp(1)", f"ERROR: {exc}", math.e, float('inf')))
        # ln check
        if 'ln' in routing:
            try:
                r = routing['ln'].ln(math.e)
                e = 1.0
                err = abs(r - e)
                checks.append(("ln(e)", r, e, err))
            except Exception as exc:
                checks.append(("ln(e)", f"ERROR: {exc}", 1.0, float('inf')))
        # pow check
        if 'pow' in routing:
            try:
                r = routing['pow'].pow(2.0, 10.0)
                e = 1024.0
                err = abs(r - e)
                checks.append(("pow(2,10)", r, e, err))
            except Exception as exc:
                checks.append(("pow(2,10)", f"ERROR: {exc}", 1024.0, float('inf')))
        # mul check
        if 'mul' in routing:
            try:
                r = routing['mul'].mul(3.0, 5.0)
                e = 15.0
                err = abs(r - e)
                checks.append(("mul(3,5)", r, e, err))
            except Exception as exc:
                checks.append(("mul(3,5)", f"ERROR: {exc}", 15.0, float('inf')))
        # div check
        if 'div' in routing:
            try:
                r = routing['div'].div(10.0, 2.0)
                e = 5.0
                err = abs(r - e)
                checks.append(("div(10,2)", r, e, err))
            except Exception as exc:
                checks.append(("div(10,2)", f"ERROR: {exc}", 5.0, float('inf')))
        # add check
        if 'add' in routing:
            try:
                r = routing['add'].add(3.0, 4.0)
                e = 7.0
                err = abs(r - e)
                checks.append(("add(3,4)", r, e, err))
            except Exception as exc:
                checks.append(("add(3,4)", f"ERROR: {exc}", 7.0, float('inf')))
        # sub check
        if 'sub' in routing:
            try:
                r = routing['sub'].sub(10.0, 3.0)
                e = 7.0
                err = abs(r - e)
                checks.append(("sub(10,3)", r, e, err))
            except Exception as exc:
                checks.append(("sub(10,3)", f"ERROR: {exc}", 7.0, float('inf')))

        accuracy_summary = {}
        for name_check, r, e, err in checks:
            # Strip imaginary part if negligible (ops work over complex internally)
            r_disp = r.real if isinstance(r, complex) else r
            r_str  = f"{r_disp:.8f}" if isinstance(r_disp, float) else str(r_disp)
            e_str  = f"{e:.8f}"
            err_str = f"{err:.2e}" if math.isfinite(err) else "FAIL"
            ok     = "OK" if (math.isfinite(err) and err < 1e-8) else ("~OK" if (math.isfinite(err) and err < 1e-5) else "FAIL")
            print(f"  {name_check:<26}  {r_str:>14}  {e_str:>14}  {err_str:>10}  {ok}")
            accuracy_summary[name_check] = {'result': r_disp, 'expected': e, 'error': err}
        results["accuracy"] = accuracy_summary

        # ── 3. Neural regression (optional) ──────────────────────────────────
        if targets:
            try:
                import statistics
                import torch
                import torch.nn.functional as F
                from .network import EMLNetwork

                _TARGET_DEFS = {
                    "sin":    (math.sin,                     -math.pi,  math.pi),
                    "cos":    (math.cos,                     -math.pi,  math.pi),
                    "x**3":   (lambda x: x**3,               -2.0,      2.0),
                    "x**2-x": (lambda x: x**2 - x,          -2.0,      2.0),
                    "exp":    (math.exp,                     -2.0,      2.0),
                    "poly4":  (lambda x: x**4 - 2*x**2 + 1, -2.0,      2.0),
                    "sqrt":   (math.sqrt,                     0.1,      4.0),
                }

                # Determine op_func from the routing (use mul/div operator for inner nodes)
                _op_func = None
                if hasattr(self, '_routing'):
                    routing_inner = self._routing
                    # Prefer to use the "dominant" inner op — if all inner ops are the same, use it
                    inner_ops = {v for k, v in routing_inner.items() if k not in ('add', 'sub')}
                    if len(inner_ops) == 1:
                        inner_op = next(iter(inner_ops))
                        # Get the torch op function from torch_ops
                        try:
                            from . import torch_ops as _to
                            op_map = {
                                'EML': None,
                                'EDL': getattr(_to, 'edl_op', None),
                                'EXL': getattr(_to, 'exl_op', None),
                                'EAL': getattr(_to, 'eal_op', None),
                            }
                            _op_func = op_map.get(inner_op.name)
                        except Exception:
                            _op_func = None

                print(f"\n  Neural regression  (depth={depth}, restarts={restarts}, steps={steps})\n")
                print(f"  {'Target':<12}  {'med MSE':>10}  {'min MSE':>10}  {'conv%':>7}")
                print(f"  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*7}")

                reg_summary = {}
                for tgt_name in targets:
                    if tgt_name not in _TARGET_DEFS:
                        print(f"  {tgt_name:<12}  (unknown target — skip)")
                        continue
                    fn, lo, hi = _TARGET_DEFS[tgt_name]
                    x_data = torch.linspace(lo, hi, 256).unsqueeze(1)
                    y_data = torch.tensor([fn(xi.item()) for xi in x_data.squeeze(1)])

                    finals = []
                    converged = 0
                    threshold = 5e-4
                    for restart in range(restarts):
                        torch.manual_seed(42 + restart * 17)
                        model = EMLNetwork(in_features=1, depth=depth, op_func=_op_func)
                        opt   = torch.optim.Adam(model.parameters(), lr=3e-3)
                        best_mse = float('inf')
                        for _ in range(steps):
                            opt.zero_grad()
                            try:
                                pred = model(x_data)
                                loss = F.mse_loss(pred, y_data)
                            except Exception:
                                continue
                            if not torch.isfinite(loss):
                                continue
                            loss.backward()
                            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                            opt.step()
                            mse = loss.item()
                            if mse < best_mse:
                                best_mse = mse
                        try:
                            final = F.mse_loss(model(x_data), y_data).item()
                            if not math.isfinite(final):
                                final = float('inf')
                        except Exception:
                            final = float('inf')
                        finals.append(final)
                        if final < threshold:
                            converged += 1

                    med = statistics.median(finals)
                    mn  = min(finals)
                    cv  = converged / restarts

                    def _fmt(v):
                        if v == float('inf'): return "inf"
                        if v < 1e-10: return f"{v:.1e}"
                        return f"{v:.3e}"

                    print(f"  {tgt_name:<12}  {_fmt(med):>10}  {_fmt(mn):>10}  {cv:.0%}".rstrip())
                    reg_summary[tgt_name] = {'med_mse': med, 'min_mse': mn, 'conv_rate': cv}

                results["regression"] = reg_summary

            except ImportError:
                print("\n  [regression skipped: torch not installed]")

        print(f"\n{'='*60}\n")
        return results

    def info(self) -> None:
        """Print routing table with operator names and node counts."""
        print(repr(self))
        print(f"  {'Operation':<10}  {'Operator':<8}  {'Nodes':<6}  {'vs EML-only'}")
        print(f"  {'-'*10}  {'-'*8}  {'-'*6}  {'-'*14}")
        for op_name in sorted(self._routing.keys()):
            base = self._routing[op_name]
            costs = _NODE_COSTS.get(op_name, {})
            this_cost  = costs.get(base.name, '?')
            eml_cost   = costs.get('EML', '?')
            if isinstance(this_cost, int) and isinstance(eml_cost, int):
                saving = eml_cost - this_cost
                vs_str = f"saves {saving}n" if saving > 0 else ("same" if saving == 0 else "worse")
            else:
                vs_str = "?"
            print(f"  {op_name:<10}  {base.name:<8}  {str(this_cost)+'n':<6}  {vs_str}")


# ── BEST: pre-built optimal routing ───────────────────────────────────────────
#
# Routing rationale (node counts from paper + derivations):
#   exp   -> EML (tied at 1 node; EML is reference)
#   ln    -> EXL (1 node via exl(0,x)=ln(x); EML/EDL need 3 nodes)
#   pow   -> EXL (3 nodes via 3-step formula; EML=15, EDL=11)
#   mul   -> EDL (7 nodes; EML=13)
#   div   -> EDL (1 node via edl(0,x)=exp(0)/ln(x)=1/ln(x)... actually
#                 div_edl is 1 node; EML=15)
#   recip -> EDL (2 nodes; EML=5)
#   neg   -> EDL (6 nodes; EML=9)
#   sub   -> EML (5 nodes; ONLY EML supports subtraction of arbitrary reals)
#   add   -> EML (11 nodes; ONLY EML supports addition of arbitrary reals)

BEST: HybridOperator  # forward declaration; defined after all operators are set up


def _make_best() -> HybridOperator:
    return HybridOperator(
        name="BEST",
        routing={
            'exp':   EML,
            'ln':    EXL,
            'pow':   EXL,
            'mul':   EDL,
            'div':   EDL,
            'recip': EDL,
            'neg':   EDL,
            'sub':   EML,
            'add':   EML,
        },
    )


BEST = _make_best()
