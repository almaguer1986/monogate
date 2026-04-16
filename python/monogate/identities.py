"""
monogate.identities — Rich catalog of mathematical identities for EML proof benchmarking.

Provides Identity dataclass and categorized lists of known identities spanning
trigonometric, hyperbolic, exponential, special, physics, and EML-structural forms.

Public API
----------
Identity                  — frozen dataclass for one identity
TRIG_IDENTITIES           — list of trigonometric identities
HYPERBOLIC_IDENTITIES     — list of hyperbolic identities
EXPONENTIAL_IDENTITIES    — list of exponential/logarithmic identities
SPECIAL_IDENTITIES        — list of special-function identities
PHYSICS_IDENTITIES        — list of physics identities
EML_IDENTITIES            — list of EML structural identities
OPEN_IDENTITIES           — list of open/hard challenges
ALL_IDENTITIES            — union of all above

get_by_difficulty(difficulty) -> list[Identity]
get_by_category(category)     -> list[Identity]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

__all__ = [
    "Identity",
    "TRIG_IDENTITIES",
    "HYPERBOLIC_IDENTITIES",
    "EXPONENTIAL_IDENTITIES",
    "SPECIAL_IDENTITIES",
    "PHYSICS_IDENTITIES",
    "EML_IDENTITIES",
    "OPEN_IDENTITIES",
    "ALL_IDENTITIES",
    "get_by_difficulty",
    "get_by_category",
]

PI = math.pi


@dataclass(frozen=True)
class Identity:
    """A mathematical identity with metadata for benchmarking.

    Args:
        name:            Short human-readable label.
        expression:      Parseable identity string (split on ``==``).
        latex:           LaTeX representation of the identity.
        category:        One of 'trigonometric', 'hyperbolic', 'exponential',
                         'special', 'physics', 'eml', 'open'.
        domain:          (lo, hi) interval on which to test the identity.
        difficulty:      One of 'trivial', 'easy', 'medium', 'hard', 'open'.
        notes:           Optional human notes.
        expected_method: Expected proof method: 'exact', 'numerical', 'unknown'.
    """

    name: str
    expression: str
    latex: str
    category: str
    domain: tuple
    difficulty: str
    notes: str = ""
    expected_method: str = "exact"


# ── Trigonometric identities ──────────────────────────────────────────────────

TRIG_IDENTITIES: List[Identity] = [
    Identity(
        name="Pythagorean identity",
        expression="sin(x)**2 + cos(x)**2 == 1",
        latex=r"\sin^2(x) + \cos^2(x) = 1",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        notes="Fundamental trig identity",
        expected_method="exact",
    ),
    Identity(
        name="Double-angle sine",
        expression="sin(2*x) == 2*sin(x)*cos(x)",
        latex=r"\sin(2x) = 2\sin(x)\cos(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Double-angle cosine",
        expression="cos(2*x) == cos(x)**2 - sin(x)**2",
        latex=r"\cos(2x) = \cos^2(x) - \sin^2(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Cosine double-angle alt",
        expression="cos(2*x) == 1 - 2*sin(x)**2",
        latex=r"\cos(2x) = 1 - 2\sin^2(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Power reduction sine",
        expression="sin(x)**2 == (1 - cos(2*x))/2",
        latex=r"\sin^2(x) = \frac{1 - \cos(2x)}{2}",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Power reduction cosine",
        expression="cos(x)**2 == (1 + cos(2*x))/2",
        latex=r"\cos^2(x) = \frac{1 + \cos(2x)}{2}",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Tan squared identity",
        expression="1 + tan(x)**2 == 1/cos(x)**2",
        latex=r"1 + \tan^2(x) = \sec^2(x)",
        category="trigonometric",
        domain=(-1.4, 1.4),
        difficulty="medium",
        notes="Domain avoids cos(x)=0",
        expected_method="exact",
    ),
    Identity(
        name="Triple-angle sine",
        expression="sin(3*x) == 3*sin(x) - 4*sin(x)**3",
        latex=r"\sin(3x) = 3\sin(x) - 4\sin^3(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Triple-angle cosine",
        expression="cos(3*x) == 4*cos(x)**3 - 3*cos(x)",
        latex=r"\cos(3x) = 4\cos^3(x) - 3\cos(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Sine product identity",
        expression="sin(x)*sin(x) == (1 - cos(2*x))/2",
        latex=r"\sin(x)\sin(x) = \frac{1-\cos(2x)}{2}",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Cosine sum identity (y=1)",
        expression="cos(x + 1) == cos(x)*cos(1) - sin(x)*sin(1)",
        latex=r"\cos(x+1) = \cos(x)\cos(1) - \sin(x)\sin(1)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        notes="Sum formula with y=1 fixed",
        expected_method="numerical",
    ),
    Identity(
        name="Sine sum identity (y=1)",
        expression="sin(x + 1) == sin(x)*cos(1) + cos(x)*sin(1)",
        latex=r"\sin(x+1) = \sin(x)\cos(1) + \cos(x)\sin(1)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        notes="Sum formula with y=1 fixed",
        expected_method="numerical",
    ),
    Identity(
        name="Sine squared minus cosine squared",
        expression="sin(x)**2 - cos(x)**2 == -cos(2*x)",
        latex=r"\sin^2(x) - \cos^2(x) = -\cos(2x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Product-to-sum cosines",
        expression="2*cos(x)*cos(x) == 1 + cos(2*x)",
        latex=r"2\cos(x)\cos(x) = 1 + \cos(2x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Sine of pi minus x",
        expression="sin(3.141592653589793 - x) == sin(x)",
        latex=r"\sin(\pi - x) = \sin(x)",
        category="trigonometric",
        domain=(0.0, PI),
        difficulty="easy",
        expected_method="numerical",
    ),
    Identity(
        name="Cosine negation",
        expression="cos(-x) == cos(x)",
        latex=r"\cos(-x) = \cos(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="trivial",
        notes="Even function property",
        expected_method="exact",
    ),
    Identity(
        name="Sine negation",
        expression="sin(-x) == -sin(x)",
        latex=r"\sin(-x) = -\sin(x)",
        category="trigonometric",
        domain=(-PI, PI),
        difficulty="trivial",
        notes="Odd function property",
        expected_method="exact",
    ),
]

# ── Hyperbolic identities ─────────────────────────────────────────────────────

HYPERBOLIC_IDENTITIES: List[Identity] = [
    Identity(
        name="Hyperbolic Pythagorean",
        expression="cosh(x)**2 - sinh(x)**2 == 1",
        latex=r"\cosh^2(x) - \sinh^2(x) = 1",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Double-angle sinh",
        expression="sinh(2*x) == 2*sinh(x)*cosh(x)",
        latex=r"\sinh(2x) = 2\sinh(x)\cosh(x)",
        category="hyperbolic",
        domain=(-2.0, 2.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Double-angle cosh",
        expression="cosh(2*x) == cosh(x)**2 + sinh(x)**2",
        latex=r"\cosh(2x) = \cosh^2(x) + \sinh^2(x)",
        category="hyperbolic",
        domain=(-2.0, 2.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Tanh definition",
        expression="tanh(x) == sinh(x)/cosh(x)",
        latex=r"\tanh(x) = \frac{\sinh(x)}{\cosh(x)}",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Sech squared",
        expression="1 - tanh(x)**2 == 1/cosh(x)**2",
        latex=r"1 - \tanh^2(x) = \operatorname{sech}^2(x)",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Cosh power reduction",
        expression="cosh(x)**2 == (cosh(2*x) + 1)/2",
        latex=r"\cosh^2(x) = \frac{\cosh(2x)+1}{2}",
        category="hyperbolic",
        domain=(-2.0, 2.0),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Sinh power reduction",
        expression="sinh(x)**2 == (cosh(2*x) - 1)/2",
        latex=r"\sinh^2(x) = \frac{\cosh(2x)-1}{2}",
        category="hyperbolic",
        domain=(-2.0, 2.0),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Tanh double angle",
        expression="tanh(2*x) == 2*tanh(x)/(1 + tanh(x)**2)",
        latex=r"\tanh(2x) = \frac{2\tanh(x)}{1+\tanh^2(x)}",
        category="hyperbolic",
        domain=(-2.0, 2.0),
        difficulty="medium",
        expected_method="exact",
    ),
    Identity(
        name="Cosh plus sinh",
        expression="cosh(x) + sinh(x) == exp(x)",
        latex=r"\cosh(x) + \sinh(x) = e^x",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Cosh minus sinh",
        expression="cosh(x) - sinh(x) == exp(-x)",
        latex=r"\cosh(x) - \sinh(x) = e^{-x}",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Sinh negation",
        expression="sinh(-x) == -sinh(x)",
        latex=r"\sinh(-x) = -\sinh(x)",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="Odd function property",
        expected_method="exact",
    ),
    Identity(
        name="Cosh negation",
        expression="cosh(-x) == cosh(x)",
        latex=r"\cosh(-x) = \cosh(x)",
        category="hyperbolic",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="Even function property",
        expected_method="exact",
    ),
]

# ── Exponential / Logarithmic identities ──────────────────────────────────────

EXPONENTIAL_IDENTITIES: List[Identity] = [
    Identity(
        name="Exp times exp-neg",
        expression="exp(x) * exp(-x) == 1",
        latex=r"e^x \cdot e^{-x} = 1",
        category="exponential",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        expected_method="exact",
    ),
    Identity(
        name="Log of exp",
        expression="log(exp(x)) == x",
        latex=r"\ln(e^x) = x",
        category="exponential",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        expected_method="exact",
    ),
    Identity(
        name="Exp of log",
        expression="exp(log(x)) == x",
        latex=r"e^{\ln(x)} = x",
        category="exponential",
        domain=(0.1, 5.0),
        difficulty="trivial",
        notes="Domain restricted to x>0",
        expected_method="exact",
    ),
    Identity(
        name="Exp sum (y=1)",
        expression="exp(x + 1) == exp(x)*exp(1)",
        latex=r"e^{x+1} = e^x \cdot e",
        category="exponential",
        domain=(-2.0, 2.0),
        difficulty="trivial",
        expected_method="numerical",
    ),
    Identity(
        name="Log product (y=2)",
        expression="log(x*2) == log(x) + log(2)",
        latex=r"\ln(2x) = \ln(x) + \ln(2)",
        category="exponential",
        domain=(0.1, 5.0),
        difficulty="easy",
        expected_method="numerical",
    ),
    Identity(
        name="Log power",
        expression="log(x**2) == 2*log(x)",
        latex=r"\ln(x^2) = 2\ln(x)",
        category="exponential",
        domain=(0.1, 5.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Log of reciprocal",
        expression="log(1/x) == -log(x)",
        latex=r"\ln(1/x) = -\ln(x)",
        category="exponential",
        domain=(0.1, 5.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Exp double",
        expression="exp(2*x) == exp(x)**2",
        latex=r"e^{2x} = (e^x)^2",
        category="exponential",
        domain=(-2.0, 2.0),
        difficulty="easy",
        expected_method="exact",
    ),
    Identity(
        name="Exp negation",
        expression="exp(-x) == 1/exp(x)",
        latex=r"e^{-x} = \frac{1}{e^x}",
        category="exponential",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        expected_method="exact",
    ),
    Identity(
        name="Exp zero",
        expression="exp(0) == 1",
        latex=r"e^0 = 1",
        category="exponential",
        domain=(0.0, 0.0),
        difficulty="trivial",
        notes="Constant identity",
        expected_method="exact",
    ),
    Identity(
        name="Log one",
        expression="log(1) == 0",
        latex=r"\ln(1) = 0",
        category="exponential",
        domain=(1.0, 1.0),
        difficulty="trivial",
        notes="Constant identity",
        expected_method="exact",
    ),
    Identity(
        name="Log exp-chain",
        expression="log(exp(x) + exp(-x)) == log(2*cosh(x))",
        latex=r"\ln(e^x + e^{-x}) = \ln(2\cosh(x))",
        category="exponential",
        domain=(-2.0, 2.0),
        difficulty="medium",
        expected_method="exact",
    ),
]

# ── Special function identities ───────────────────────────────────────────────

SPECIAL_IDENTITIES: List[Identity] = [
    Identity(
        name="Lgamma recurrence",
        expression="lgamma(x + 1) == lgamma(x) + log(x)",
        latex=r"\ln\Gamma(x+1) = \ln\Gamma(x) + \ln(x)",
        category="special",
        domain=(0.5, 5.0),
        difficulty="medium",
        notes="Gamma function recurrence; log-form",
        expected_method="exact",
    ),
    Identity(
        name="Lgamma at 1",
        expression="lgamma(1) == 0",
        latex=r"\ln\Gamma(1) = 0",
        category="special",
        domain=(1.0, 1.0),
        difficulty="trivial",
        notes="Gamma(1)=1",
        expected_method="exact",
    ),
    Identity(
        name="Lgamma at 2",
        expression="lgamma(2) == 0",
        latex=r"\ln\Gamma(2) = 0",
        category="special",
        domain=(2.0, 2.0),
        difficulty="trivial",
        notes="Gamma(2)=1",
        expected_method="exact",
    ),
    Identity(
        name="Erf odd symmetry",
        expression="erf(x) == -erf(-x)",
        latex=r"\mathrm{erf}(x) = -\mathrm{erf}(-x)",
        category="special",
        domain=(-2.0, 2.0),
        difficulty="easy",
        notes="erf is an odd function",
        expected_method="exact",
    ),
    Identity(
        name="Erf at zero",
        expression="erf(0) == 0",
        latex=r"\mathrm{erf}(0) = 0",
        category="special",
        domain=(0.0, 0.0),
        difficulty="trivial",
        expected_method="exact",
    ),
    Identity(
        name="Erf squared plus erfc squared (approx)",
        expression="erf(x)**2 + (1 - erf(x))**2 == erf(x)**2 + 1 - 2*erf(x) + erf(x)**2",
        latex=r"\mathrm{erf}^2(x) + \mathrm{erfc}^2(x) = 2\mathrm{erf}^2(x) - 2\mathrm{erf}(x) + 1",
        category="special",
        domain=(-2.0, 2.0),
        difficulty="easy",
        notes="Algebraic identity on erf/erfc",
        expected_method="exact",
    ),
    Identity(
        name="Bessel J0 at zero",
        expression="j0(0) == 1",
        latex=r"J_0(0) = 1",
        category="special",
        domain=(0.0, 0.0),
        difficulty="trivial",
        notes="j0 is math.j0",
        expected_method="numerical",
    ),
    Identity(
        name="Fresnel symmetry S",
        expression="fresnel_s(x) == -fresnel_s(-x)",
        latex=r"S(x) = -S(-x)",
        category="special",
        domain=(-3.0, 3.0),
        difficulty="easy",
        notes="Fresnel S is odd",
        expected_method="numerical",
    ),
    Identity(
        name="Fresnel symmetry C",
        expression="fresnel_c(x) == -fresnel_c(-x)",
        latex=r"C(x) = -C(-x)",
        category="special",
        domain=(-3.0, 3.0),
        difficulty="easy",
        notes="Fresnel C is odd",
        expected_method="numerical",
    ),
    Identity(
        name="Digamma shift",
        expression="digamma(x + 1) == digamma(x) + 1/x",
        latex=r"\psi(x+1) = \psi(x) + \frac{1}{x}",
        category="special",
        domain=(0.5, 5.0),
        difficulty="medium",
        expected_method="numerical",
    ),
    Identity(
        name="Lgamma symmetry check",
        expression="lgamma(x) == lgamma(x + 1) - log(x)",
        latex=r"\ln\Gamma(x) = \ln\Gamma(x+1) - \ln(x)",
        category="special",
        domain=(0.5, 5.0),
        difficulty="easy",
        expected_method="numerical",
    ),
    Identity(
        name="Erf sum identity",
        expression="erf(x) + erf(-x) == 0",
        latex=r"\mathrm{erf}(x) + \mathrm{erf}(-x) = 0",
        category="special",
        domain=(-2.0, 2.0),
        difficulty="trivial",
        notes="Odd function; sum is zero",
        expected_method="exact",
    ),
]

# ── Physics identities ────────────────────────────────────────────────────────

PHYSICS_IDENTITIES: List[Identity] = [
    Identity(
        name="Schrodinger unitarity",
        expression="cos(x)**2 + sin(x)**2 == 1",
        latex=r"|e^{ix}|^2 = \cos^2(x) + \sin^2(x) = 1",
        category="physics",
        domain=(-PI, PI),
        difficulty="easy",
        notes="|exp(ix)|² = 1 (quantum unitarity); equivalent to Pythagorean",
        expected_method="exact",
    ),
    Identity(
        name="Heat kernel even symmetry",
        expression="exp(-x**2/4) == exp(-(-x)**2/4)",
        latex=r"K(x,t=1) = K(-x,t=1)",
        category="physics",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="Heat kernel is even in x",
        expected_method="exact",
    ),
    Identity(
        name="Wave cosine even parity",
        expression="cos(x) == cos(-x)",
        latex=r"\cos(x) = \cos(-x)",
        category="physics",
        domain=(-PI, PI),
        difficulty="trivial",
        notes="Even parity of wave function",
        expected_method="exact",
    ),
    Identity(
        name="NLS soliton amplitude",
        expression="1/cosh(x)**2 == 4*exp(2*x)/(exp(2*x)+1)**2",
        latex=r"\operatorname{sech}^2(x) = \frac{4e^{2x}}{(e^{2x}+1)^2}",
        category="physics",
        domain=(-3.0, 3.0),
        difficulty="hard",
        notes="NLS soliton amplitude in exp form",
        expected_method="exact",
    ),
    Identity(
        name="Free particle energy conservation",
        expression="exp(x)**2 + exp(-x)**2 == 2*cosh(2*x)",
        latex=r"e^{2x} + e^{-2x} = 2\cosh(2x)",
        category="physics",
        domain=(-2.0, 2.0),
        difficulty="easy",
        notes="Energy-like combination",
        expected_method="exact",
    ),
    Identity(
        name="KdV symmetry",
        expression="1/cosh(x)**2 == 1/cosh(-x)**2",
        latex=r"\operatorname{sech}^2(x) = \operatorname{sech}^2(-x)",
        category="physics",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="KdV soliton is even",
        expected_method="exact",
    ),
    Identity(
        name="Gaussian normalization factor",
        expression="exp(-x**2) == exp(-(-x)**2)",
        latex=r"e^{-x^2} = e^{-(-x)^2}",
        category="physics",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="Gaussian is an even function",
        expected_method="exact",
    ),
]

# ── EML structural identities ─────────────────────────────────────────────────

EML_IDENTITIES: List[Identity] = [
    Identity(
        name="EML exp representation",
        expression="exp(x) == exp(x) - log(1)",
        latex=r"e^x = e^x - \ln(1) = \mathrm{eml}(x, 1)",
        category="eml",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        notes="eml(x,1) = exp(x) since log(1)=0",
        expected_method="exact",
    ),
    Identity(
        name="EML log representation",
        expression="log(x) == exp(0) - (exp(0) - log(x))",
        latex=r"\ln(x) = 1 - \mathrm{eml}(0, x)",
        category="eml",
        domain=(0.1, 5.0),
        difficulty="easy",
        notes="eml(0,x) = 1 - log(x), so log(x) = 1 - eml(0,x)",
        expected_method="exact",
    ),
    Identity(
        name="EML multiplication",
        expression="exp(x) * exp(y) == exp(x + y)",
        latex=r"e^x \cdot e^y = e^{x+y}",
        category="eml",
        domain=(-2.0, 2.0),
        difficulty="trivial",
        notes="Fundamental EML mul identity (y=1 fixed numerically)",
        expected_method="exact",
    ),
    Identity(
        name="EML self-inverse",
        expression="exp(x - x) == 1",
        latex=r"e^{x-x} = 1",
        category="eml",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        expected_method="exact",
    ),
    Identity(
        name="EML constant leaf",
        expression="exp(0) == 1",
        latex=r"e^0 = 1",
        category="eml",
        domain=(0.0, 0.0),
        difficulty="trivial",
        notes="The fundamental leaf-1 representation",
        expected_method="exact",
    ),
    Identity(
        name="EML negation via log",
        expression="-log(exp(x)) == -x",
        latex=r"-\ln(e^x) = -x",
        category="eml",
        domain=(-3.0, 3.0),
        difficulty="trivial",
        expected_method="exact",
    ),
]

# ── Open challenge identities ─────────────────────────────────────────────────

OPEN_IDENTITIES: List[Identity] = [
    Identity(
        name="Sin EML witness existence",
        expression="sin(x)**2 + cos(x)**2 == 1",
        latex=r"\sin^2(x) + \cos^2(x) = 1",
        category="open",
        domain=(-PI, PI),
        difficulty="open",
        notes="Can MCTS find a short EML witness for this identity?",
        expected_method="unknown",
    ),
    Identity(
        name="Euler reflection",
        expression="sin(3.141592653589793*x) == 3.141592653589793*x",
        latex=r"\sin(\pi x) \approx \pi x",
        category="open",
        domain=(-0.1, 0.1),
        difficulty="open",
        notes="Small-angle approximation; requires deep tree for exact EML",
        expected_method="numerical",
    ),
    Identity(
        name="Stirling approximation",
        expression="lgamma(x + 1) == x*log(x) - x + 0.5*log(2*3.141592653589793*x)",
        latex=r"\ln\Gamma(x+1) \approx x\ln(x) - x + \frac{1}{2}\ln(2\pi x)",
        category="open",
        domain=(5.0, 20.0),
        difficulty="open",
        notes="Stirling approximation; approximate only",
        expected_method="numerical",
    ),
    Identity(
        name="EML phantom attractor",
        expression="exp(x) == exp(x - 0.0001) * exp(0.0001)",
        latex=r"e^x = e^{x-\epsilon} \cdot e^{\epsilon}",
        category="open",
        domain=(-2.0, 2.0),
        difficulty="open",
        notes="Testing MCTS escape from phantom attractor",
        expected_method="numerical",
    ),
    Identity(
        name="Deep sin representation",
        expression="sin(x) == sin(x)",
        latex=r"\sin(x) = \sin(x)",
        category="open",
        domain=(-PI, PI),
        difficulty="open",
        notes="Can any EML tree represent sin(x) exactly? Proven impossible in finite depth.",
        expected_method="unknown",
    ),
]

# ── Combined catalog ──────────────────────────────────────────────────────────

ALL_IDENTITIES: List[Identity] = (
    TRIG_IDENTITIES
    + HYPERBOLIC_IDENTITIES
    + EXPONENTIAL_IDENTITIES
    + SPECIAL_IDENTITIES
    + PHYSICS_IDENTITIES
    + EML_IDENTITIES
    + OPEN_IDENTITIES
)


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_by_difficulty(difficulty: str) -> List[Identity]:
    """Return all identities with the given difficulty level.

    Args:
        difficulty: One of 'trivial', 'easy', 'medium', 'hard', 'open'.

    Returns:
        List of matching Identity objects.
    """
    return [i for i in ALL_IDENTITIES if i.difficulty == difficulty]


def get_by_category(category: str) -> List[Identity]:
    """Return all identities in the given category.

    Args:
        category: One of 'trigonometric', 'hyperbolic', 'exponential',
                  'special', 'physics', 'eml', 'open'.

    Returns:
        List of matching Identity objects.
    """
    return [i for i in ALL_IDENTITIES if i.category == category]
