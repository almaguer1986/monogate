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

__version__ = "0.12.0"

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

from .optimize import (  # noqa: F401
    best_optimize,
    optimize,
    OptimizeResult,
    OpMatch,
    BenchmarkResult,
    benchmark_optimize,
    sin_eml_taylor,
    sin_best_taylor,
    cos_best_taylor,
    gelu_eml_approx,
    gelu_best_approx,
    LayerOptimizeResult,
    ModelOptimizeReport,
    best_optimize_model,
    optimize_siren,
    optimize_nerf,
    context_aware_best_optimize,
    ContextAwareResult,
    StabilityWarning,
)

__all__ += [
    "best_optimize", "optimize", "OptimizeResult", "OpMatch",
    "BenchmarkResult", "benchmark_optimize",
    "sin_eml_taylor", "sin_best_taylor", "cos_best_taylor",
    "gelu_eml_approx", "gelu_best_approx",
    "LayerOptimizeResult", "ModelOptimizeReport", "best_optimize_model",
    "optimize_siren", "optimize_nerf",
    "context_aware_best_optimize", "ContextAwareResult", "StabilityWarning",
]

try:
    from .torch_ops import edl_op_safe, EDL_SAFE_CONSTANT  # noqa: F401
    __all__ += ["edl_op_safe", "EDL_SAFE_CONSTANT"]
except ImportError:
    pass

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

try:
    from .torch import EMLActivation, EMLLayer  # noqa: F401

    __all__ += ["EMLActivation", "EMLLayer"]
except ImportError:
    pass  # torch not installed

from .complex_eval import (  # noqa: F401
    eml_complex,
    eval_complex,
    euler_path_node,
    sin_via_euler,
    cos_via_euler,
    score_complex_projection,
    formula_complex,
    COMPLEX_TERMINALS,
)

__all__ += [
    "eml_complex",
    "eval_complex",
    "euler_path_node",
    "sin_via_euler",
    "cos_via_euler",
    "score_complex_projection",
    "formula_complex",
    "COMPLEX_TERMINALS",
]

try:
    from .compile import (  # noqa: F401
        FusedEMLActivation, FusedEMLLayer,
        compile_eml_layer, to_torchscript,
        benchmark_layer, BenchmarkTable,
    )
    __all__ += [
        "FusedEMLActivation", "FusedEMLLayer",
        "compile_eml_layer", "to_torchscript",
        "benchmark_layer", "BenchmarkTable",
    ]
except ImportError:
    pass  # torch not installed

from .llm import suggest_and_optimize, LLMOptimizeResult  # noqa: F401

__all__ += ["suggest_and_optimize", "LLMOptimizeResult"]

from .validate import validate_submission, ValidationResult, load_problems, list_problems  # noqa: F401

__all__ += ["validate_submission", "ValidationResult", "load_problems", "list_problems"]

from .complex_best import (  # noqa: F401
    ComplexHybridOperator,
    CBEST,
    ComplexOptimizeResult,
    complex_best_optimize,
    im,
    re,
    SIN_NODE_COUNT,
    COS_NODE_COUNT,
    J0_NODE_COUNT,
    AI_NODE_COUNT,
    ERF_NODE_COUNT,
)

__all__ += [
    "ComplexHybridOperator",
    "CBEST",
    "ComplexOptimizeResult",
    "complex_best_optimize",
    "im",
    "re",
    "SIN_NODE_COUNT",
    "COS_NODE_COUNT",
    "J0_NODE_COUNT",
    "AI_NODE_COUNT",
    "ERF_NODE_COUNT",
]

from .complex_search import (  # noqa: F401
    complex_mcts_search,
    complex_beam_search,
    ComplexMCTSResult,
    ComplexBeamResult,
)

__all__ += [
    "complex_mcts_search",
    "complex_beam_search",
    "ComplexMCTSResult",
    "ComplexBeamResult",
]

try:
    from .pinn import EMLPINN, PINNResult, fit_pinn  # noqa: F401
    __all__ += ["EMLPINN", "PINNResult", "fit_pinn"]
except ImportError:
    pass  # torch not installed

from .special import (  # noqa: F401
    SpecialFnEntry,
    CATALOG as SPECIAL_CATALOG,
    sin_cb, cos_cb,
    sinh_cb, cosh_cb, tanh_cb, sech_cb,
    erf_cb,
    fresnel_s_integrand_cb, fresnel_c_integrand_cb,
    fresnel_s_cb, fresnel_c_cb,
    j0_cb, ai_cb,
    lgamma_cb, digamma_cb,
    catalog_summary, save_catalog,
)

__all__ += [
    "SpecialFnEntry",
    "SPECIAL_CATALOG",
    "sin_cb", "cos_cb",
    "sinh_cb", "cosh_cb", "tanh_cb", "sech_cb",
    "erf_cb",
    "fresnel_s_integrand_cb", "fresnel_c_integrand_cb",
    "fresnel_s_cb", "fresnel_c_cb",
    "j0_cb", "ai_cb",
    "lgamma_cb", "digamma_cb",
    "catalog_summary", "save_catalog",
]

from .interval import (  # noqa: F401
    Interval,
    eml_interval,
    eval_interval,
    bound_expression,
)

__all__ += [
    "Interval",
    "eml_interval",
    "eval_interval",
    "bound_expression",
]

try:
    from .sympy_bridge import (  # noqa: F401
        to_sympy,
        from_sympy,
        simplify_eml,
        latex_eml,
        verify_identity,
    )
    __all__ += [
        "to_sympy",
        "from_sympy",
        "simplify_eml",
        "latex_eml",
        "verify_identity",
    ]
except ImportError:
    pass  # sympy not installed — bridge unavailable

from .leaderboard import (  # noqa: F401
    BenchmarkProblem,
    LeaderboardEntry,
    PROBLEMS,
    run_leaderboard,
    print_leaderboard,
    markdown_leaderboard,
    save_leaderboard,
    load_leaderboard,
)

__all__ += [
    "BenchmarkProblem",
    "LeaderboardEntry",
    "PROBLEMS",
    "run_leaderboard",
    "print_leaderboard",
    "markdown_leaderboard",
    "save_leaderboard",
    "load_leaderboard",
]
