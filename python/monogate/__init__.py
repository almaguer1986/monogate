"""
monogate — Exp-Minus-Log arithmetic.

    eml(x, y) = exp(x) − ln(y)

From this single binary operator and the constant 1, every elementary
arithmetic function can be constructed as a pure expression tree.

Reference: arXiv:2603.21852 (Odrzywołek, 2026) · CC BY 4.0

Core functions (no dependencies):
    op, E, ZERO, NEG_ONE,
    exp_eml, ln_eml, sub_eml, neg_eml,
    add_eml, mul_eml, div_eml, pow_eml, recip_eml,
    IDENTITIES

Neural network classes (requires torch):
    EMLTree, EMLNetwork, fit
"""

from .core import (
    op,
    E,
    ZERO,
    NEG_ONE,
    exp_eml,
    ln_eml,
    sub_eml,
    neg_eml,
    add_eml,
    mul_eml,
    div_eml,
    pow_eml,
    recip_eml,
    IDENTITIES,
    Operator,
    EML,
    EDL,
    make_exp,
    make_ln,
    exp_edl,
    ln_edl,
)

__version__ = "0.2.0"

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
    "make_exp",
    "make_ln",
    "exp_edl",
    "ln_edl",
    "__version__",
]

try:
    from .network import EMLTree, EMLNetwork, fit  # noqa: F401

    __all__ += ["EMLTree", "EMLNetwork", "fit"]
except ImportError:
    pass  # torch not installed — network classes unavailable
