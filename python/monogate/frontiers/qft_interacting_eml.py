"""
Session 75 — QFT & Path Integrals: Interacting Theories

φ⁴ theory, Feynman rules, renormalization, running coupling, asymptotic freedom,
and confinement classified through the EML depth hierarchy.

Key theorem: The running coupling constant in QFT is EML-2 in the perturbative
regime; the confinement transition (diverging coupling) is an EML-∞ transition —
a direct instance of the EML Phase Transition Theorem.
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
# φ⁴ theory EML structure
# ---------------------------------------------------------------------------

@dataclass
class PhiFourTheory:
    """
    φ⁴ scalar field theory:
    S[φ] = ∫d⁴x [½(∂μφ)² + ½m²φ² + λ/4! φ⁴]

    EML analysis of each term:
    - ½(∂μφ)²: kinetic term, EML-2 in φ (quadratic)
    - ½m²φ²: mass term, EML-2 (quadratic)
    - λ/4! φ⁴: interaction vertex, EML-2 (degree-4 polynomial)
    - Full action: EML-2 in φ

    Feynman rules:
    - Propagator Δ(p) = 1/(p²+m²): EML-2 (rational function of p)
    - Vertex: -λ (EML-0 coupling constant)
    - Loop integral: ∫d⁴k/((k²+m²)((k+p)²+m²)) → logarithmically divergent

    The loop divergence is EML-2: ln(Λ/m) where Λ = UV cutoff.
    """
    m: float = 1.0     # mass
    lam: float = 0.1   # coupling constant

    def propagator(self, p: float) -> float:
        """Feynman propagator Δ(p) = 1/(p²+m²)"""
        return 1.0 / (p ** 2 + self.m ** 2)

    def one_loop_integral_log(self, Lambda: float = 100.0) -> dict:
        """
        One-loop correction to 2-point function (bubble diagram):
        ∫_{|k|<Λ} d⁴k/((k²+m²)²) ≈ π²·[Λ² - m²·ln(Λ²/m²) - m²]

        Divergent parts: Λ² (quadratic) and ln(Λ) (logarithmic).
        EML depth of ln(Λ/m): EML-2 (single ln gate).
        """
        log_div = math.log(Lambda ** 2 / self.m ** 2)
        quad_div = Lambda ** 2
        finite_part = -self.m ** 2
        return {
            "Lambda": Lambda,
            "quadratic_divergence": round(quad_div, 2),
            "log_divergence_coefficient": round(log_div, 4),
            "finite_part": round(finite_part, 4),
            "eml_log_divergence": 2,
            "reason": "ln(Λ/m) = EML-2 (ln gate); Λ² = EML-0 (polynomial in cutoff)",
        }

    def one_loop_mass_correction(self, Lambda: float = 100.0) -> dict:
        """
        δm² ≈ λ/(16π²) · [Λ² - m²·ln(Λ²/m²)]
        After renormalization: m_R² = m² + δm²
        """
        integral = self.one_loop_integral_log(Lambda)
        delta_m_sq = self.lam / (16 * math.pi ** 2) * (Lambda ** 2 - self.m ** 2 * integral["log_divergence_coefficient"])
        return {
            "delta_m_squared": round(delta_m_sq, 4),
            "eml_depth": 2,
            "reason": "λ·ln(Λ/m) — coupling times EML-2 log = EML-2",
        }

    def to_dict(self) -> dict:
        ps = [0.1, 0.5, 1.0, 2.0, 5.0]
        return {
            "theory": "φ⁴ scalar field theory",
            "mass": self.m,
            "coupling": self.lam,
            "propagator_values": {str(p): round(self.propagator(p), 6) for p in ps},
            "one_loop_integral": self.one_loop_integral_log(Lambda=100.0),
            "mass_correction": self.one_loop_mass_correction(Lambda=100.0),
            "action_eml_depth": 2,
            "propagator_eml_depth": 2,
            "vertex_eml_depth": 0,
            "loop_divergence_eml_depth": 2,
        }


# ---------------------------------------------------------------------------
# Running coupling and RG flow
# ---------------------------------------------------------------------------

@dataclass
class RunningCoupling:
    """
    Renormalization group (RG) flow of coupling constant λ(μ):

    Callan-Symanzik equation: μ·∂λ/∂μ = β(λ)

    For φ⁴ in d=4:
    β(λ) = 3λ²/(16π²) + O(λ³)  [positive → Landau pole, IR-free]

    Solution at one-loop:
    λ(μ) = λ₀ / (1 - 3λ₀/(16π²) · ln(μ/μ₀))

    EML depth: λ(μ) = EML-2 (rational function of ln(μ/μ₀))

    For QCD (non-abelian gauge theory):
    β(g) = -b₀g³/(16π²) + O(g⁵)  [negative → asymptotic freedom]
    g²(μ) = g²(μ₀) / (1 + b₀g²(μ₀)/(8π²) · ln(μ/μ₀))
    → EML-2 (same form)

    Confinement: g(μ) → ∞ as μ → 0 → EML-∞ transition
    """
    lambda_0: float = 0.1   # coupling at scale μ₀
    beta_0: float = 3 / (16 * math.pi ** 2)  # one-loop β coefficient for φ⁴

    def running_coupling(self, mu: float, mu_0: float = 1.0) -> float:
        """λ(μ) = λ₀ / (1 - β₀λ₀ ln(μ/μ₀))"""
        log_ratio = math.log(mu / mu_0)
        denom = 1 - self.beta_0 * self.lambda_0 * log_ratio
        if abs(denom) < 1e-10:
            return float("inf")  # Landau pole
        return self.lambda_0 / denom

    def landau_pole(self, mu_0: float = 1.0) -> float:
        """μ* where coupling diverges: ln(μ*/μ₀) = 1/(β₀·λ₀)"""
        return mu_0 * math.exp(1.0 / (self.beta_0 * self.lambda_0))

    def eml_depth_vs_scale(self) -> dict:
        mu_values = [0.1, 0.5, 1.0, 2.0, 10.0, 100.0]
        couplings = []
        for mu in mu_values:
            lam = self.running_coupling(mu)
            eml = 2 if lam < 1e10 else "∞"
            couplings.append({"mu": mu, "lambda_mu": round(lam, 6), "eml_depth": eml})
        return {
            "lambda_0": self.lambda_0,
            "beta_0": round(self.beta_0, 8),
            "landau_pole_mu": round(self.landau_pole(), 4),
            "formula": "λ(μ) = λ₀/(1 - β₀λ₀ln(μ/μ₀)) [EML-2]",
            "coupling_vs_scale": couplings,
            "eml_perturbative": "EML-2 (rational function of ln(μ))",
            "eml_landau_pole": "EML-∞ (coupling diverges → EML Phase Transition)",
        }


@dataclass
class AsymptoticFreedom:
    """
    QCD running coupling: g²(μ) = g²(μ₀)/(1 + b₀·g²(μ₀)/(8π²)·ln(μ/μ₀))

    b₀ = 11 - 2n_f/3 > 0 for n_f < 16.5 (negative β → asymptotic freedom)

    At large μ (UV): g²(μ) → 0 → quarks are free → EML-2 (small coupling)
    At small μ (IR): g²(μ) → ∞ → confinement → EML-∞ transition

    The confinement scale Λ_QCD where g² diverges:
    Λ_QCD = μ₀ · exp(-8π²/(b₀·g²(μ₀)))
    """
    g_sq_0: float = 0.5     # g²(μ₀)
    n_f: int = 6             # number of quark flavors
    mu_0: float = 91.2       # Z-mass reference scale (GeV)

    @property
    def b_0(self) -> float:
        return 11 - 2 * self.n_f / 3

    def running_g_sq(self, mu: float) -> float:
        """g²(μ) = g²(μ₀) / (1 + b₀·g²/(8π²)·ln(μ/μ₀))"""
        log_ratio = math.log(mu / self.mu_0)
        denom = 1 + self.b_0 * self.g_sq_0 / (8 * math.pi ** 2) * log_ratio
        if denom <= 1e-10:
            return float("inf")
        return self.g_sq_0 / denom

    def qcd_scale(self) -> float:
        """Λ_QCD = μ₀·exp(-8π²/(b₀·g²(μ₀)))"""
        return self.mu_0 * math.exp(-8 * math.pi ** 2 / (self.b_0 * self.g_sq_0))

    def to_dict(self) -> dict:
        mu_values = [0.5, 1.0, 5.0, 10.0, 91.2, 1000.0]
        coupling_values = []
        for mu in mu_values:
            g_sq = self.running_g_sq(mu)
            eml = "∞" if g_sq > 1e10 else 2
            coupling_values.append({"mu_GeV": mu, "g_squared": round(g_sq, 6), "alpha_s": round(g_sq / (4 * math.pi), 6), "eml_depth": eml})
        return {
            "n_f": self.n_f,
            "b_0": round(self.b_0, 4),
            "g_sq_0": self.g_sq_0,
            "mu_0_GeV": self.mu_0,
            "lambda_qcd_GeV": round(self.qcd_scale(), 4),
            "coupling_vs_scale": coupling_values,
            "eml_uv": "EML-2: g²(μ)→0 as μ→∞ (asymptotic freedom = EML-2 running)",
            "eml_ir": "EML-∞: g²(μ)→∞ as μ→Λ_QCD (confinement = EML Phase Transition)",
            "theorem": (
                "Confinement EML Theorem: "
                "The confinement transition in QCD occurs at μ=Λ_QCD where g(μ)→∞. "
                "This is an EML-∞ transition in exactly the sense of the EML Phase Transition Theorem (Session 57): "
                "the coupling g(μ) as a function of μ becomes EML-∞ at μ=Λ_QCD."
            ),
        }


# ---------------------------------------------------------------------------
# Feynman diagrams and EML depth
# ---------------------------------------------------------------------------

@dataclass
class FeynmanDiagramEML:
    """
    EML depth of Feynman diagram contributions.

    Tree-level diagrams: finite combination of EML-0 (vertices) and EML-2 (propagators) → EML-2
    One-loop: EML-2 × ln(Λ) = EML-2 (log divergence)
    L-loop: EML-2 × [ln(Λ)]^L = EML-2 (polynomial in ln)
    Non-perturbative (instantons): exp(-1/g²) → EML-1 in 1/g² → essential singularity → EML-∞ in g→0
    """

    @staticmethod
    def instanton_amplitude(g_sq: float) -> float:
        """exp(-S_instanton/g²) = exp(-8π²/g²) — essential singularity in g"""
        return math.exp(-8 * math.pi ** 2 / g_sq)

    @staticmethod
    def classify_diagram(n_loops: int, has_instanton: bool = False) -> EMLClass:
        if has_instanton:
            return EMLClass(EML_INF, "non-perturbative (instanton)", "exp(-8π²/g²) — essential singularity in g → EML-∞")
        if n_loops == 0:
            return EMLClass(2, f"tree-level", "Product of propagators 1/(p²+m²) = EML-2")
        return EMLClass(2, f"{n_loops}-loop", f"loop integrals → EML-2 (polynomial in ln(Λ/m) at {n_loops} loops)")

    def diagram_table(self) -> list[dict]:
        table = []
        for n_loops in range(4):
            eml = self.classify_diagram(n_loops)
            table.append({
                "diagram_type": f"{'tree' if n_loops==0 else str(n_loops)+'-loop'}",
                "contribution_structure": "Π propagators × vertices" if n_loops == 0 else f"∫d⁴k × propagators × vertices",
                "divergence": "finite" if n_loops == 0 else f"polynomial in ln(Λ) of degree {n_loops}",
                "eml_depth": str(eml),
            })
        # Instanton
        eml_inst = self.classify_diagram(0, has_instanton=True)
        table.append({
            "diagram_type": "instanton",
            "contribution_structure": "exp(-8π²/g²) × polynomial corrections",
            "divergence": "essential singularity at g=0 (non-perturbative)",
            "eml_depth": str(eml_inst),
        })
        return table

    def instanton_series(self, g_sq_values: list[float]) -> dict:
        return {
            "formula": "A_instanton = exp(-8π²/g²) [EML-∞ in g as g→0]",
            "values": [
                {"g_sq": g_sq, "amplitude": round(self.instanton_amplitude(g_sq), 8)}
                for g_sq in g_sq_values
            ],
            "eml_class": "EML-∞",
            "reason": "exp(-8π²/g²) has an essential singularity at g=0 — not expandable in powers of g",
        }


# ---------------------------------------------------------------------------
# EML Taxonomy for QFT
# ---------------------------------------------------------------------------

QFT_INTERACTING_EML_TAXONOMY: dict[str, dict] = {
    "phi4_action": {
        "eml_depth": 2,
        "description": "φ⁴ action S[φ] = ∫[½(∂φ)²+½m²φ²+λφ⁴/4!]d⁴x",
        "reason": "Polynomial in φ up to degree 4 → EML-2",
    },
    "feynman_propagator": {
        "eml_depth": 2,
        "description": "Δ(p) = 1/(p²+m²)",
        "reason": "Rational function of p → EML-2",
    },
    "vertex_factor": {
        "eml_depth": 0,
        "description": "Coupling -λ at 4-point vertex",
        "reason": "Constant = EML-0",
    },
    "loop_integral_log": {
        "eml_depth": 2,
        "description": "∫d⁴k/((k²+m²)²) ~ ln(Λ/m)",
        "reason": "Logarithmic UV divergence: ln gate → EML-2",
    },
    "running_coupling": {
        "eml_depth": 2,
        "description": "λ(μ) = λ₀/(1-β₀λ₀ln(μ/μ₀))",
        "reason": "Rational function of ln(μ) → EML-2",
    },
    "landau_pole": {
        "eml_depth": "∞",
        "description": "λ(μ*)→∞ at Landau pole μ* = μ₀exp(1/(β₀λ₀))",
        "reason": "EML Phase Transition: coupling diverges → EML-∞",
    },
    "asymptotic_freedom": {
        "eml_depth": 2,
        "description": "QCD: g²(μ)→0 as μ→∞",
        "reason": "g²(μ) = g²₀/(1+b₀g²₀ln(μ/μ₀)/(8π²)) — EML-2 rational-in-log",
    },
    "qcd_confinement": {
        "eml_depth": "∞",
        "description": "g(μ)→∞ as μ→Λ_QCD",
        "reason": "EML Phase Transition: g diverges at Λ_QCD — same EML-∞ class as phase transitions (Session 57)",
    },
    "instanton_amplitude": {
        "eml_depth": "∞",
        "description": "A ~ exp(-8π²/g²) — non-perturbative",
        "reason": "Essential singularity at g=0: cannot be expressed as EML-finite function of g",
    },
    "renormalized_mass": {
        "eml_depth": 2,
        "description": "m_R² = m² + δm² where δm² ~ λln(Λ/m)",
        "reason": "Linear in λ times EML-2 (log) = EML-2",
    },
}


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_qft_interacting_eml() -> dict:
    """Run full Session 75 analysis."""

    # 1. φ⁴ theory
    phi4 = PhiFourTheory(m=1.0, lam=0.1)
    phi4_report = phi4.to_dict()

    # 2. Running coupling (φ⁴)
    rc = RunningCoupling(lambda_0=0.1)
    rc_report = rc.eml_depth_vs_scale()

    # 3. Asymptotic freedom (QCD)
    qcd = AsymptoticFreedom(g_sq_0=0.5, n_f=6, mu_0=91.2)
    qcd_report = qcd.to_dict()

    # 4. Feynman diagram EML table
    fd = FeynmanDiagramEML()
    fd_table = fd.diagram_table()
    instanton = fd.instanton_series([0.5, 1.0, 2.0, 4.0])

    # 5. Taxonomy
    taxonomy = QFT_INTERACTING_EML_TAXONOMY

    return {
        "session": 75,
        "title": "QFT & Path Integrals: Interacting Theories",
        "key_theorem": {
            "theorem": "QFT Confinement = EML Phase Transition Theorem",
            "statement": (
                "The confinement transition in QCD is an EML-∞ transition: "
                "the running coupling g(μ) is EML-2 for μ > Λ_QCD (perturbative regime) "
                "and EML-∞ at μ = Λ_QCD (coupling diverges). "
                "This is exactly the EML Phase Transition Theorem (Session 57) applied to QFT: "
                "the free energy analog (effective potential V_eff) becomes EML-∞ at the confinement scale."
            ),
            "corollary_instantons": (
                "Non-perturbative QFT effects (instantons) are EML-∞ in the coupling g: "
                "exp(-8π²/g²) has an essential singularity at g=0 — it is invisible to "
                "all orders of perturbation theory (Taylor expansion in g). "
                "The EML-∞ barrier separates perturbative (EML-2) from non-perturbative physics."
            ),
        },
        "phi4_theory": phi4_report,
        "running_coupling_phi4": rc_report,
        "qcd_asymptotic_freedom": qcd_report,
        "feynman_diagram_eml": fd_table,
        "instanton_amplitude": instanton,
        "taxonomy": taxonomy,
        "eml_depth_summary": {
            "EML-0": "Coupling constants λ, g at vertices; color factors",
            "EML-2": "Propagators, loop integrals, running coupling, renormalized parameters",
            "EML-3": "Path integral in position space: exp(-S) = EML-1; full propagator ∫dk → EML-3 (Green's function)",
            "EML-∞": "Landau pole (λ→∞), confinement (g→∞ at Λ_QCD), instantons exp(-1/g²)",
        },
        "connections": {
            "to_session_57": "Confinement = EML Phase Transition (same theorem as Ising at T_c)",
            "to_session_61": "Session 61 free field QFT: EML-1 amplitudes. Session 75: interactions add EML-2 corrections.",
            "to_session_60": "Running coupling A(μ) = EML-2 = same class as log partition function A(θ) in info theory",
            "to_session_64": "Feynman-Kac (Session 64): same EML-1 → EML-3 bridge via path integral",
        },
    }


if __name__ == "__main__":
    result = analyze_qft_interacting_eml()
    print(json.dumps(result, indent=2, default=str))
