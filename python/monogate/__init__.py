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
    HybridOperator,
    BEST,
    EML,
    EDL,
    EMN,
    EXL,
    EAL,
    make_exp,
    make_ln,
    exp_edl,
    ln_edl,
    recip_edl,
    neg_edl,
    div_edl,
    mul_edl,
    pow_edl,
    EDL_ONE,
    EDL_NEG_ONE,
    compare_op,
)

__version__ = "0.3.0"

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
    "HybridOperator",
    "BEST",
    "EML",
    "EDL",
    "EMN",
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
    "EXL",
    "EAL",
    "pow_exl",
    "compare_op",
    "__version__",
]

from .optimize import best_optimize, optimize, OptimizeResult, OpMatch  # noqa: F401

__all__ += ["best_optimize", "optimize", "OptimizeResult", "OpMatch"]

from .torch_ops import edl_op_safe, EDL_SAFE_CONSTANT  # noqa: F401

__all__ += ["edl_op_safe", "EDL_SAFE_CONSTANT"]

from .operators import (
    ALL_OPERATORS,
    COMPLETE_OPERATORS,
    get_operator,
    compare_all,
    markdown_table,
)

__all__ += [
    "ALL_OPERATORS",
    "COMPLETE_OPERATORS",
    "get_operator",
    "compare_all",
    "markdown_table",
]

try:
    from .network import EMLTree, EMLNetwork, HybridNetwork, fit  # noqa: F401

    __all__ += ["EMLTree", "EMLNetwork", "HybridNetwork", "fit"]
except ImportError:
    pass  # torch not installed — network classes unavailable
