"""
Session 124 — Graph Theory & Networks: Spectral Properties, Percolation & Dynamic Networks

Laplacian spectra, random walk mixing, bond/site percolation, epidemic spreading on
networks, network rewiring, and temporal networks classified by EML depth.

Key theorem: Graph Laplacian eigenvalues λ_k = 2(1-cos(πk/n)) for path graph = EML-3
(trigonometric of rational). Algebraic connectivity λ₂ (Fiedler) = EML-2 (controls
mixing via log(n)/λ₂). Percolation threshold p_c = ⟨k⟩/⟨k²⟩ = EML-2 (ratio of moments).
Scale-free β_c → 0 as ⟨k²⟩→∞ = EML-∞ (cascade divergence).
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class SpectralGraphTheory:
    """
    Laplacian spectra and spectral graph theory.

    EML structure:
    - Path graph Laplacian eigenvalues: λ_k = 2(1-cos(πk/n)): EML-3 (trig of rational)
    - Cycle graph: same eigenvalues with k=0,1,...,n-1: EML-3
    - Complete graph K_n: λ₁=0, λ₂=...=λ_n=n: EML-0
    - Star graph S_n: λ₁=0, λ₂=...=λ_{n-1}=1, λ_n=n: EML-0
    - Mixing time: τ_mix ~ (1/λ₂)·ln(n): EML-2 (log n scaled by EML-2 spectral gap)
    - Heat kernel: K_t(u,v) = Σ_k exp(-λ_k t)·φ_k(u)φ_k(v): EML-1 (sum of EML-1 terms)
    - Cheeger constant h(G): EML-2 by Cheeger inequality λ₂/2 ≤ h ≤ √(2λ₂)
    """

    def path_eigenvalues(self, n: int) -> dict:
        """λ_k = 2(1-cos(πk/n)) for k=0,...,n-1."""
        eigs = [2 * (1 - math.cos(math.pi * k / n)) for k in range(n)]
        fiedler = sorted(eigs)[1]  # second smallest
        return {
            "n": n,
            "eigenvalues": [round(e, 4) for e in eigs[:8]],
            "lambda_1_fiedler": round(fiedler, 4),
            "lambda_max": round(max(eigs), 4),
            "eml": 3,
            "reason": "λ_k=2(1-cos(πk/n)): trig of rational argument = EML-3.",
        }

    def mixing_time(self, fiedler: float, n: int) -> dict:
        """τ_mix ~ (1/λ₂)·ln(n)."""
        tau = math.log(n) / fiedler
        return {
            "fiedler_lambda2": fiedler,
            "n_vertices": n,
            "tau_mix_approx": round(tau, 2),
            "eml": 2,
            "reason": "τ~ln(n)/λ₂: logarithm of n divided by eigenvalue = EML-2.",
        }

    def heat_kernel_trace(self, t: float, n: int) -> dict:
        """Tr(exp(-tL)) = Σ_k exp(-λ_k t) for path graph."""
        eigs = [2 * (1 - math.cos(math.pi * k / n)) for k in range(n)]
        trace = sum(math.exp(-e * t) for e in eigs)
        return {
            "t": t, "n": n,
            "Tr_exp_minus_tL": round(trace, 4),
            "eml": 1,
            "reason": "Tr(e^{-tL})=Σ_k exp(-λ_k t): sum of EML-1 heat terms = EML-1.",
        }

    def cheeger_bounds(self, fiedler: float) -> dict:
        """λ₂/2 ≤ h(G) ≤ √(2λ₂): Cheeger inequality."""
        lower = fiedler / 2
        upper = math.sqrt(2 * fiedler)
        return {
            "lambda2": fiedler,
            "h_lower_bound": round(lower, 4),
            "h_upper_bound": round(upper, 4),
            "eml": 2,
            "reason": "Cheeger: h~√λ₂: square root of EML-2 = EML-2.",
        }

    def to_dict(self) -> dict:
        return {
            "path_eigenvalues": [self.path_eigenvalues(n) for n in [5, 10, 20]],
            "mixing_time": [self.mixing_time(f, n) for f, n in
                            [(0.1, 100), (0.01, 1000), (1.0, 50)]],
            "heat_kernel_trace": [self.heat_kernel_trace(t, 10) for t in [0.1, 0.5, 1.0, 5.0]],
            "cheeger": [self.cheeger_bounds(f) for f in [0.01, 0.1, 0.5, 1.0]],
            "eml_path_spectrum": 3,
            "eml_mixing_time": 2,
            "eml_heat_kernel": 1,
            "eml_cheeger": 2,
        }


@dataclass
class PercolationTheory:
    """
    Bond and site percolation on networks.

    EML structure:
    - Bond percolation: each edge retained with probability p
    - p_c for ER: p_c = 1/⟨k⟩ = 1/(n·p_edge): EML-0 (reciprocal of degree)
    - Giant component size: S ~ (p-p_c)^β with β=1: EML-2 (linear near threshold)
    - Below p_c: S~0, correlation length ξ~|p-p_c|^{-ν}: EML-2 (power law divergence)
    - At p_c: S ~ n^{-β/ν}: EML-2 (power law in n)
    - Epidemic on networks: β_c = ⟨k⟩/⟨k²⟩: EML-2 (ratio of moments)
    - Scale-free ⟨k²⟩→∞: β_c→0 = EML-∞ (any infection spreads)
    """

    def er_percolation(self, p: float, n: int = 1000, k_avg: float = 5.0) -> dict:
        """ER random graph: p_c = 1/k_avg. Giant component S~(p-p_c) for p>p_c."""
        p_c = 1.0 / k_avg
        if p < p_c:
            S = 0.0
            regime = "subcritical"
            eml = 1
        elif abs(p - p_c) < 0.01 * p_c:
            S = n ** (-1.0 / 3)
            regime = "critical"
            eml = EML_INF
        else:
            excess = p - p_c
            S = 2 * excess / p_c
            S = min(S, 1.0)
            regime = "supercritical"
            eml = 2
        return {
            "p": p, "p_c": round(p_c, 4), "n": n,
            "S_giant": round(S, 4),
            "regime": regime,
            "eml": "∞" if eml == EML_INF else eml,
            "reason_sub": "S=0: EML-0 (trivial). Reason_sup: S~(p-p_c): linear in excess = EML-2.",
        }

    def epidemic_threshold(self, k_moments: dict) -> dict:
        """β_c = ⟨k⟩/⟨k²⟩ for SIS on network."""
        k1 = k_moments["k1"]
        k2 = k_moments["k2"]
        if k2 == 0:
            return {"beta_c": float("inf"), "eml": 0}
        beta_c = k1 / k2
        eml = 2 if k2 < float("inf") else EML_INF
        return {
            "k1_mean_degree": k1,
            "k2_mean_sq_degree": k2,
            "beta_c": round(beta_c, 6),
            "eml": "∞" if eml == EML_INF else eml,
            "reason": "β_c=⟨k⟩/⟨k²⟩: ratio of moments = EML-2. Scale-free ⟨k²⟩→∞: β_c→0 = EML-∞.",
        }

    def correlation_length(self, p: float, p_c: float = 0.2, nu: float = 4.0 / 3) -> dict:
        """ξ ~ |p-p_c|^{-ν}: correlation length diverges at p_c."""
        delta = abs(p - p_c)
        if delta < 1e-6:
            return {"p": p, "xi": float("inf"), "eml": "∞"}
        xi = delta ** (-nu)
        return {
            "p": p, "p_c": p_c,
            "xi": round(xi, 4),
            "eml": 2,
            "reason": f"ξ~|p-p_c|^{{-{nu}}}: power law divergence = EML-2.",
        }

    def to_dict(self) -> dict:
        p_vals = [0.1, 0.18, 0.199, 0.2, 0.21, 0.3, 0.5]
        return {
            "er_percolation": [self.er_percolation(p, k_avg=5.0) for p in p_vals],
            "epidemic_threshold": [
                self.epidemic_threshold({"k1": 4.0, "k2": 20.0}),
                self.epidemic_threshold({"k1": 3.0, "k2": 1000.0}),
                self.epidemic_threshold({"k1": 2.0, "k2": float("inf")}),
            ],
            "correlation_length": [self.correlation_length(p) for p in [0.1, 0.15, 0.199, 0.201, 0.3]],
            "eml_subcritical": 0,
            "eml_supercritical": 2,
            "eml_critical": "∞",
            "eml_scale_free_threshold": "∞",
        }


@dataclass
class DynamicNetworks:
    """
    Temporal and adaptive networks: rewiring, cascades, synchronization.

    EML structure:
    - Rewiring: if edge (u,v) rewires at rate r → memory kernel exp(-rt) = EML-1
    - Kuramoto synchronization: r(t)=|Σ exp(iθ_j)|/N: EML-3 (phase = trig)
    - Synchronization threshold: K_c = 2/π·g(0): EML-2 (ratio involving freq density)
    - Cascade threshold (Watts): φ_c = 1/k_avg: EML-0 (reciprocal of degree, same as p_c)
    - Network collapse cascade: EML-∞ (system-size cascade = phase transition)
    - Temporal motifs: exponential inter-event time P(τ)=λ·exp(-λτ): EML-1
    """

    def kuramoto_order(self, thetas: list[float]) -> dict:
        """Order parameter r = |Σ exp(iθ_j)|/N."""
        N = len(thetas)
        re = sum(math.cos(t) for t in thetas) / N
        im = sum(math.sin(t) for t in thetas) / N
        r = math.sqrt(re**2 + im**2)
        psi = math.atan2(im, re)
        return {
            "N": N,
            "r": round(r, 4),
            "psi_rad": round(psi, 4),
            "eml": 3,
            "reason": "r=|Σexp(iθ_j)|/N: modulus of sum of complex exponentials = EML-3 (trig of phases).",
        }

    def synchronization_threshold(self, g_omega_0: float) -> dict:
        """K_c = 2/(π·g(0)) for Lorentzian freq distribution."""
        K_c = 2.0 / (math.pi * g_omega_0)
        return {
            "g_omega_0": g_omega_0,
            "K_c": round(K_c, 4),
            "eml_K_c": 2,
            "eml_threshold": "∞",
            "reason": "K_c=2/(π·g(0)): reciprocal of frequency density = EML-2. Crossing K_c = EML-∞.",
        }

    def inter_event_time(self, tau: float, lam: float = 0.1) -> dict:
        """Temporal network: P(τ) = λ·exp(-λτ): exponential inter-event time."""
        P = lam * math.exp(-lam * tau)
        return {
            "tau": tau, "lambda": lam,
            "P_tau": round(P, 6),
            "eml": 1,
            "reason": "P(τ)=λexp(-λτ): EML-1 (Poisson process memory kernel).",
        }

    def to_dict(self) -> dict:
        thetas_sync = [i * 2 * math.pi / 10 + 0.1 for i in range(10)]
        thetas_unsync = [i * 2 * math.pi / 10 for i in range(10)]
        return {
            "kuramoto_order": [
                self.kuramoto_order(thetas_sync),
                self.kuramoto_order(thetas_unsync),
                self.kuramoto_order([0.0] * 10),
            ],
            "sync_threshold": [self.synchronization_threshold(g) for g in [0.1, 0.5, 1.0]],
            "inter_event_time": [self.inter_event_time(t) for t in [0, 5, 10, 20, 50]],
            "eml_kuramoto_order": 3,
            "eml_sync_threshold": "∞",
            "eml_temporal_motifs": 1,
            "eml_cascade_collapse": "∞",
        }


def analyze_graph_deep_eml() -> dict:
    sg = SpectralGraphTheory()
    pt = PercolationTheory()
    dn = DynamicNetworks()
    return {
        "session": 124,
        "title": "Graph Theory & Networks: Spectral Properties, Percolation & Dynamic Networks",
        "key_theorem": {
            "theorem": "EML Network Phase Transition Theorem",
            "statement": (
                "Path graph Laplacian eigenvalues λ_k=2(1-cos(πk/n)) are EML-3 (trig of rational). "
                "Mixing time τ~ln(n)/λ₂ is EML-2. "
                "Heat kernel Tr(exp(-tL)) is EML-1 (sum of Boltzmann terms). "
                "ER percolation giant component S~(p-p_c) is EML-2 above threshold. "
                "Correlation length ξ~|p-p_c|^{-ν} is EML-2 (power law divergence). "
                "Percolation threshold p=p_c is EML-∞. "
                "Network epidemic threshold β_c=⟨k⟩/⟨k²⟩ is EML-2; scale-free β_c→0 is EML-∞. "
                "Kuramoto order parameter r=|Σexp(iθ)/N| is EML-3. "
                "Synchronization threshold K_c is EML-∞."
            ),
        },
        "spectral_graph_theory": sg.to_dict(),
        "percolation_theory": pt.to_dict(),
        "dynamic_networks": dn.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Cascade threshold φ_c=1/k_avg; complete/star graph spectra; trivial giant component S=0",
            "EML-1": "Heat kernel Tr(exp(-tL)); inter-event time P(τ)=λexp(-λτ); post-collapse rebound",
            "EML-2": "Mixing time ln(n)/λ₂; Cheeger h~√λ₂; percolation S~(p-p_c); ξ~|p-p_c|^{-ν}; β_c=⟨k⟩/⟨k²⟩",
            "EML-3": "Laplacian spectrum 2(1-cos(πk/n)); Kuramoto order r=|Σexp(iθ)|/N",
            "EML-∞": "Percolation threshold p=p_c; sync threshold K_c; scale-free β_c→0; cascade collapse",
        },
        "rabbit_hole_log": [
            "The graph Laplacian spectrum is EML-3 because the path graph is a discretized 1D Schrödinger operator. The eigenvalues λ_k = 2(1-cos(πk/n)) = 4sin²(πk/2n) are EML-3 (squared trig) — the same EML-3 as phonon dispersion |sin(ka/2)| on a crystal lattice (S108) and diffraction sinc² patterns (S116). The discrete Fourier transform and the path graph Laplacian share the same EML-3 eigenvalue structure because both are instances of the discrete derivative operator on periodic domains.",
            "The Kuramoto model synchronization transition is the social analog of the ferromagnetic phase transition: the order parameter r = |Σ exp(iθ_j)|/N is EML-3 (complex exponential modulus), and it undergoes an EML-∞ transition at K=K_c. Below K_c: r=0 (incoherence = EML-0). Above K_c: r grows as √(K-K_c) = EML-2 (same as Ising magnetization near T_c). The synchronization phase transition is EML-∞, exactly like Ising (S57), percolation (this session), and epidemic threshold (S113).",
            "Scale-free networks (Barabási-Albert, γ<3) have ⟨k²⟩→∞ as N→∞. The epidemic threshold β_c=⟨k⟩/⟨k²⟩→0: any finite infection rate causes an epidemic. This is an EML-∞ effect: the mean-field epidemic threshold vanishes because the degree heterogeneity (variance = ⟨k²⟩-⟨k⟩²) diverges. The same EML-2 power law (P(k)~k^{-γ}) that makes scale-free networks robust to random failures (high-degree hubs survive) makes them fragile to targeted attacks (remove hubs → percolation threshold p_c→0).",
        ],
        "connections": {
            "to_session_104": "S104 covered ER, scale-free, PageRank at overview. S124 adds Laplacian spectra (EML-3), mixing times, percolation, Kuramoto.",
            "to_session_57": "Kuramoto sync transition (EML-∞) = Ising phase transition (EML-∞): same universality class.",
            "to_session_113": "Network β_c=⟨k⟩/⟨k²⟩ = S113 epidemic threshold. Scale-free β_c→0 = EML-∞ epidemic spread.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_graph_deep_eml(), indent=2, default=str))
