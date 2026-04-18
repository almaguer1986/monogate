"""
Session 79 — Differential Galois Theory: Nonlinear ODEs & Painlevé Equations

Painlevé transcendents, Riccati chains, Abel equations, and the EML classification
of nonlinear ODEs via their singularity structure and integrability.

Key theorem: The Painlevé property (no movable branch points) is equivalent to
EML-finite solutions at generic points; movable singularities correspond to EML-∞.
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass, field
from typing import Optional


EML_INF = float("inf")


@dataclass
class EMLClass:
    depth: float
    label: str
    reason: str

    def __str__(self) -> str:
        d = "∞" if self.depth == EML_INF else str(int(self.depth))
        return f"EML-{d}: {self.label}"


# ---------------------------------------------------------------------------
# Painlevé equations
# ---------------------------------------------------------------------------

@dataclass
class PainleveEquation:
    """
    The six Painlevé transcendents P_I–P_VI.

    Painlevé property: all movable singularities are poles (not branch points).
    This is the nonlinear analog of Fuchs regularity.

    EML classification:
    - Solutions with Painlevé property: EML-finite in generic regions (poles = EML-2 via 1/(z-z_0))
    - At poles (movable): Laurent expansion → EML-2 singular terms
    - At fixed singularities: prescribed behavior → EML-finite
    - Global monodromy: EML-∞ (Stokes-like phenomena in nonlinear setting)

    Special solvable cases:
    P_I: y'' = 6y² + z — no known EML-finite general solution (EML-∞)
    P_II (α=0): y'' = 2y³ + zy — reduces to linear → EML-3 (Airy)
    P_IV (special params): rational solutions → EML-2
    """
    name: str
    equation: str
    parameters: dict
    painleve_property: bool
    eml_generic: float
    eml_special: float
    special_case_description: str
    solutions: list[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "equation": self.equation,
            "parameters": self.parameters,
            "painleve_property": self.painleve_property,
            "eml_generic": "∞" if self.eml_generic == EML_INF else self.eml_generic,
            "eml_special_cases": self.eml_special if self.eml_special != EML_INF else "∞",
            "special_case": self.special_case_description,
            "known_solutions": self.solutions,
        }


PAINLEVE_EQUATIONS = [
    PainleveEquation(
        "P_I",
        "y'' = 6y² + z",
        {},
        True,
        EML_INF,
        EML_INF,
        "No known elementary or EML-finite solutions. True Painlevé transcendent.",
        ["Asymptotic: y ~ ±√(-z/6) as z→-∞ (EML-2); y ~ P(z)/(z-z_0)² near poles (EML-2 Laurent)"],
    ),
    PainleveEquation(
        "P_II",
        "y'' = 2y³ + zy + α",
        {"alpha": "complex"},
        True,
        EML_INF,
        3,
        "α=0: Riccati reduction to Airy equation y'' = zy → EML-3 (Airy Ai, Bi).",
        ["α∈ℤ: rational solutions (EML-2)", "α=0: Airy functions Ai(z), Bi(z) (EML-3)", "General α: EML-∞"],
    ),
    PainleveEquation(
        "P_IV",
        "y'' = (y')²/(2y) + 3y³/2 + 4zy² + 2(z²-α)y + β/(2y)",
        {"alpha": "complex", "beta": "complex"},
        True,
        EML_INF,
        2,
        "Special parameters: rational solutions y=2z+c (EML-2), Hermite solutions.",
        ["Rational solutions for integer α,β (EML-2)", "Weber parabolic cylinder functions (EML-3)", "General: EML-∞"],
    ),
    PainleveEquation(
        "P_VI",
        "y'' = ½(1/y+1/(y-1)+1/(y-z))·(y')² - (1/z+1/(z-1)+1/(y-z))·y' + ...",
        {"alpha": "complex", "beta": "complex", "gamma": "complex", "delta": "complex"},
        True,
        EML_INF,
        2,
        "Confluence limits give P_I through P_V. Algebraic solutions for special params → EML-2.",
        ["Algebraic solutions for special params (EML-2)", "Hypergeometric ₂F₁ (EML-3)", "General: EML-∞"],
    ),
    PainleveEquation(
        "Riccati equation (solvable NL ODE)",
        "y' = P(z)·y² + Q(z)·y + R(z)",
        {},
        False,
        2,
        2,
        "Riccati reduces to linear ODE if particular solution known → EML-2 general solution.",
        ["y = -P^{-1}(u'/u)' where u'' + Qu' + PRu = 0", "u solves linear ODE → EML-2"],
    ),
]


# ---------------------------------------------------------------------------
# Movable singularities and EML-∞
# ---------------------------------------------------------------------------

@dataclass
class MovableSingularity:
    """
    Movable singularities: locations depend on initial conditions (not fixed by the equation).

    Example: y' = y² has solution y = 1/(c-z) — pole at z=c.
    The pole location c is arbitrary (movable).

    EML analysis:
    - y = 1/(c-z): EML-2 (rational function = EML-2)
    - Pole at z=c: Laurent expansion y ≈ 1/(c-z) → EML-2 near pole
    - But as z→c: y → ∞ → EML-∞ AT the pole
    - Away from pole: y is EML-2

    This is the EML version of the Painlevé property:
    - Poles (algebraic singularities): EML-2 Laurent expansion
    - Branch points (y ~ (z-c)^{p/q}): EML-2 for p/q rational (algebraic)
    - Essential singularities: EML-∞
    """

    @staticmethod
    def bernoulli_ode() -> dict:
        """y' + P(z)y = Q(z)y^n — reduces to linear via v = y^{1-n}"""
        return {
            "equation": "y' + P(z)y = Q(z)y^n",
            "substitution": "v = y^{1-n} → linear ODE for v",
            "solution": "y = (e^{(1-n)∫P·dz} · (C + (1-n)∫Q·e^{(1-n)∫P·dz}·dz))^{1/(1-n)}",
            "eml_depth": 2,
            "reason": "Reduces to linear → integral of EML-1/EML-2 → EML-2 solution",
        }

    @staticmethod
    def abel_ode() -> dict:
        """y' = f₃y³ + f₂y² + f₁y + f₀ — Abel equation of first kind"""
        return {
            "equation": "y' = f₃(z)y³ + f₂(z)y² + f₁(z)y + f₀(z)",
            "solvability": "Generally not integrable in elementary functions",
            "special_cases": [
                "f₃=0 → Riccati → EML-2",
                "f₀=0, f₁=0 → Bernoulli → EML-2",
                "Constant coefficients: explicit solution via elliptic integrals → EML-∞ generally",
            ],
            "eml_generic": "∞",
            "eml_special": 2,
            "painleve_property": False,
            "reason": "Movable branch points in generic case → not Painlevé → EML-∞",
        }

    @staticmethod
    def classify_singularity(ode_type: str) -> EMLClass:
        classifications = {
            "pole (algebraic, order m)": EMLClass(2, "Laurent pole", "1/(z-z_0)^m = EML-2 (rational)"),
            "algebraic branch point (z-z_0)^{p/q}": EMLClass(2, "algebraic branch", "exp(p/q·ln(z-z_0)) = EML-2"),
            "logarithmic branch (ln(z-z_0))": EMLClass(2, "log branch", "ln gate = EML-2"),
            "essential singularity": EMLClass(EML_INF, "essential", "exp(-1/(z-z_0)) — essential singularity = EML-∞"),
        }
        return classifications.get(ode_type, EMLClass(EML_INF, "unknown", "not classified"))


# ---------------------------------------------------------------------------
# Nonlinear Kovacic theorem (proposed)
# ---------------------------------------------------------------------------

@dataclass
class NonlinearKovacicTheorem:
    """
    Extension of Kovacic's algorithm to nonlinear ODEs.

    For linear ODEs: Kovacic decides if solutions are Liouvillian (= EML-finite).
    For nonlinear ODEs: no general algorithm exists, but structural results available.

    Proposed EML-Nonlinear Kovacic:
    - An autonomous nonlinear ODE y'=f(y) with f EML-k has solutions EML-(k+1)
      (one integration increases depth by 1)
    - y' = f(y): solution y(z) = ∫_{y_0}^{y(z)} dy/f(y) = antiderivative of 1/f
      → if f is EML-k, then 1/f is EML-k, integral is EML-(k+1) [inverse function theorem]

    Examples:
    - y' = y (f=y=EML-1 in y): solution e^z = EML-1 ✓
    - y' = y² (f=y²=EML-2 in y): solution 1/(c-z) = EML-2 ✓ (integration of EML-2 → EML-2)
    - y' = sin(y) (f=EML-3): solution z = ln|tan(y/2)| = EML-2 [depth DECREASES? No — inverse function]
    """

    @staticmethod
    def separation_of_variables(f_eml_depth: int, f_example: str) -> dict:
        """
        For y' = f(y): ∫dy/f(y) = z + C → y = (∫dy/f(y))^{-1}(z+C)
        Depth of solution = depth(∫dy/f(y)) = depth(f) or depth(f)-1 (rational case)
        """
        return {
            "ode": f"y' = f(y) where f ∈ EML-{f_eml_depth}",
            "f_example": f_example,
            "solution_method": "Separation: ∫dy/f(y) = z+C → invert",
            "integral_depth": f_eml_depth,
            "solution_depth_remark": "Inverse of EML-k antiderivative can decrease or preserve depth",
        }

    @staticmethod
    def examples() -> list[dict]:
        return [
            {
                "ode": "y' = y", "f": "y = EML-1", "solution": "y = C·e^z", "eml": 1,
                "comment": "Simplest: EML-1 → EML-1 solution",
            },
            {
                "ode": "y' = y²", "f": "y² = EML-2", "solution": "y = 1/(C-z)", "eml": 2,
                "comment": "Movable pole at z=C; solution is rational = EML-2",
            },
            {
                "ode": "y' = 1+y²", "f": "1+y² = EML-2", "solution": "y = tan(z+C)", "eml": 3,
                "comment": "∫dy/(1+y²) = arctan(y) = EML-3; inverse of arctan is tan = EML-3",
            },
            {
                "ode": "y' = y·(1-y)", "f": "y(1-y) = EML-2", "solution": "y = 1/(1+Ce^{-z})", "eml": 2,
                "comment": "Logistic equation: solution = sigmoid = EML-2 (rational in e^z)",
            },
            {
                "ode": "y'' = 6y²+z (P_I)", "f": "nonlinear", "solution": "Painlevé transcendent", "eml": "∞",
                "comment": "No EML-finite general solution; EML-∞",
            },
        ]

    def to_dict(self) -> dict:
        return {
            "theorem": "Nonlinear EML Kovacic (proposed)",
            "statement": (
                "For an autonomous ODE y' = f(y) with f ∈ EML-k: "
                "the solution satisfies EML-depth ≤ k+1 generically. "
                "Equality holds when the antiderivative ∫dy/f(y) has no depth reduction. "
                "The Painlevé transcendents (P_I–P_VI) are EML-∞ because "
                "their nonlinear structure prevents EML-finite integration."
            ),
            "examples": self.examples(),
            "open_question": (
                "Is there an EML version of the Painlevé test? "
                "I.e., can we predict EML-∞ from the singularity type without solving the ODE?"
            ),
        }


# ---------------------------------------------------------------------------
# EML depth under composition
# ---------------------------------------------------------------------------

@dataclass
class EMLCompositionRules:
    """
    How EML depth behaves under basic operations.

    These rules are the algebraic foundation of the EML hierarchy.
    """

    RULES: list[dict] = field(default_factory=lambda: [
        {"operation": "f + g", "depth": "max(depth(f), depth(g))", "example": "e^x + ln x: max(1,2) = 2"},
        {"operation": "f · g", "depth": "max(depth(f), depth(g))", "example": "e^x · x²: max(1,0) = 1"},
        {"operation": "f ∘ g", "depth": "depth(f) + depth(g) - 1 (heuristic)", "example": "ln(e^x) = x: 2+1-1=2→0"},
        {"operation": "f'(x)", "depth": "max(depth(f)-1, 0) or depth(f)", "example": "(e^x)' = e^x: depth preserved"},
        {"operation": "∫f dx", "depth": "depth(f) or depth(f)+1", "example": "∫e^x dx = e^x: depth preserved; ∫(1/x) = ln(x): 0→2"},
        {"operation": "f^{-1}(x)", "depth": "same or lower", "example": "arctan = EML-3; (arctan)^{-1} = tan = EML-3"},
        {"operation": "eml(f,g) = exp(f)-ln(g)", "depth": "max(depth(f)+1, depth(g)+1)", "example": "eml(0,e^x) = 1-x: max(1,2)=2"},
    ])

    def to_dict(self) -> dict:
        return {
            "composition_rules": self.RULES,
            "key_insight": (
                "EML depth is SUBadditive under composition: depth(f∘g) ≤ depth(f) + depth(g). "
                "Cancellations can reduce depth (e.g., ln∘exp = id: depth 2+1=3 → 0). "
                "This is why EML-k forms a filtration, not a grading."
            ),
        }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_nonlinear_galois_eml() -> dict:
    painleve_report = [p.to_dict() for p in PAINLEVE_EQUATIONS]
    movable = MovableSingularity()
    movable_report = {
        "bernoulli": movable.bernoulli_ode(),
        "abel": movable.abel_ode(),
        "singularity_types": {
            name: str(movable.classify_singularity(name))
            for name in ["pole (algebraic, order m)", "algebraic branch point (z-z_0)^{p/q}",
                         "logarithmic branch (ln(z-z_0))", "essential singularity"]
        },
    }
    kovacic = NonlinearKovacicTheorem()
    kovacic_report = kovacic.to_dict()
    composition = EMLCompositionRules()

    return {
        "session": 79,
        "title": "Differential Galois Theory: Nonlinear ODEs & Painlevé",
        "key_theorem": {
            "theorem": "Painlevé Property = EML-Finite Singularity Structure",
            "statement": (
                "An ODE has the Painlevé property (movable singularities are poles only) "
                "iff its movable singularities are EML-2 (Laurent poles = rational divergences). "
                "Movable branch points are EML-2 for algebraic exponents, EML-∞ for transcendental. "
                "The general solution of a Painlevé-type ODE is EML-∞ (transcendent); "
                "special solutions at special parameters are EML-2 or EML-3."
            ),
        },
        "painleve_equations": painleve_report,
        "movable_singularities": movable_report,
        "nonlinear_kovacic": kovacic_report,
        "composition_rules": composition.to_dict(),
        "eml_depth_summary": {
            "EML-2": "Riccati, Bernoulli solutions; rational solutions of Painlevé; movable poles",
            "EML-3": "Airy solutions (P_II, α=0); Weber parabolic cylinder; elliptic-type specials",
            "EML-∞": "General Painlevé transcendents (P_I–P_VI); Abel eq generic; y'=f(y) with EML-∞ integral",
        },
        "connections": {
            "to_session_59": "Session 59 Kovacic for linear ODEs; Session 79 extends to nonlinear",
            "to_session_73": "Stokes phenomenon = EML-∞ global; Painlevé = EML-∞ general solution",
            "to_session_66": "Complex analysis monodromy; Painlevé monodromy = nonlinear Stokes data",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_nonlinear_galois_eml(), indent=2, default=str))
