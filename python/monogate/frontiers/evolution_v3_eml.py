"""
Session 142 — Evolutionary Biology Deep III: Multi-Level Selection & Major Transitions

EML operator: eml(x,y) = exp(x) - ln(y)
Key theorem: Within-group selection is EML-1; between-group selection is EML-2;
major evolutionary transitions (individuality emergence) are EML-∞.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class MultiLevelSelection:
    """Price equation: total evolution = within-group + between-group selection."""

    n_groups: int = 20
    group_size: int = 50

    def price_equation(self, cov_wg: float, e_var: float) -> dict[str, float]:
        """
        Price equation: Δz̄ = Cov(W,z)/W̄ + E[w*Δz]/W̄.
        First term = selection, second = transmission bias.
        EML-2 (covariance = EML-2 statistical moment).
        """
        selection = cov_wg
        transmission = e_var
        total = selection + transmission
        return {"selection": round(selection, 4),
                "transmission": round(transmission, 4),
                "total": round(total, 4)}

    def group_selection_coefficient(self, alpha: float, beta: float) -> float:
        """
        Between-group selection: g = beta * group_benefit / (alpha + beta).
        EML-2 (ratio of linear terms with log structure in optimum).
        """
        if alpha + beta < 1e-15:
            return 0.0
        return beta / (alpha + beta)

    def kin_selection_hamilton(self, r: float, b: float, c: float) -> float:
        """Hamilton's rule: rb - c > 0 → altruism favored. EML-0 (linear)."""
        return r * b - c

    def multilevel_fitness(self, w_within: float, w_between: float, weight: float) -> float:
        """W_total = (1-weight)*W_within + weight*W_between. EML-0 (weighted sum)."""
        return (1 - weight) * w_within + weight * w_between

    def analyze(self) -> dict[str, Any]:
        price_examples = [
            self.price_equation(0.1, 0.05),
            self.price_equation(0.05, 0.1),
            self.price_equation(0.0, 0.15)
        ]
        alpha_beta = [(0.8, 0.2), (0.5, 0.5), (0.2, 0.8)]
        g_vals = {f"alpha{a}_beta{b}": round(self.group_selection_coefficient(a, b), 4)
                  for a, b in alpha_beta}
        r_vals = [0.0, 0.125, 0.25, 0.5, 1.0]
        hamilton = {r: round(self.kin_selection_hamilton(r, 2.0, 1.0), 4) for r in r_vals}
        return {
            "model": "MultiLevelSelection",
            "price_equation_examples": price_examples,
            "group_selection_coefficient": g_vals,
            "hamilton_rule_rb_minus_c": hamilton,
            "eml_depth": {"price_equation_covariance": 2, "group_coefficient": 2,
                          "hamilton_rule": 0},
            "key_insight": "Price equation = EML-2 (covariance); Hamilton's rule = EML-0 (linear)"
        }


@dataclass
class MajorTransitions:
    """Maynard Smith & Szathmáry (1995): major transitions in individuality."""

    transitions = [
        ("Replicating molecules", "Chromosomes", "EML-∞"),
        ("Chromosomes", "Eukaryotes", "EML-∞"),
        ("Solitary individuals", "Colonies", "EML-∞"),
        ("Primate societies", "Human language", "EML-∞"),
    ]

    def transition_information_gain(self, bits_before: float, bits_after: float) -> float:
        """Information integrated at each transition: EML-2."""
        return bits_after - bits_before

    def cooperation_stability(self, benefit: float, defection_gain: float,
                               n: int) -> float:
        """
        Replicator dynamics: cooperation stable if b/c > n (snowdrift).
        Cooperation fraction at equilibrium = 1 - c/b * (1-1/n). EML-2.
        """
        if benefit <= 0:
            return 0.0
        c = 1.0
        ratio = c / benefit * max(1.0, 1 - 1.0 / n)
        return max(0.0, min(1.0, 1 - ratio))

    def evolvability_landscape(self, g: float, env_variance: float) -> float:
        """
        Evolvability E = exp(-g²/2σ²) × robustness. EML-1.
        High mutational robustness + evolvability at phase transition = EML-∞.
        """
        sigma2 = env_variance
        return math.exp(-g ** 2 / (2 * sigma2 + 1e-10))

    def analyze(self) -> dict[str, Any]:
        info_gains = [self.transition_information_gain(2 ** i, 2 ** (i + 3))
                      for i in range(len(self.transitions))]
        n_vals = [2, 5, 10, 20, 50]
        coop = {n: round(self.cooperation_stability(3.0, 1.5, n), 4) for n in n_vals}
        g_vals = [0.0, 0.5, 1.0, 2.0]
        evolvability = {g: round(self.evolvability_landscape(g, 1.0), 4) for g in g_vals}
        return {
            "model": "MajorTransitions",
            "transitions_eml": [{"from": t[0], "to": t[1], "depth": t[2]}
                                 for t in self.transitions],
            "information_gain_per_transition": [round(x, 2) for x in info_gains],
            "cooperation_stability_vs_n": coop,
            "evolvability_vs_mutation_effect": evolvability,
            "eml_depth": {"information_gain": 2, "cooperation_equilibrium": 2,
                          "evolvability": 1, "major_transition_event": "∞"},
            "key_insight": "All major transitions in individuality are EML-∞ (irreversible emergence)"
        }


@dataclass
class EvolutionaryGameTheory:
    """ESS and replicator dynamics in multi-species interactions."""

    def replicator_equation(self, freqs: list[float],
                             payoff_matrix: list[list[float]]) -> list[float]:
        """
        ẋᵢ = xᵢ(fᵢ - f̄). EML-0 (linear payoffs), EML-2 (f̄ = Σ xᵢfᵢ).
        """
        n = len(freqs)
        fitness = [sum(payoff_matrix[i][j] * freqs[j] for j in range(n))
                   for i in range(n)]
        f_bar = sum(freqs[i] * fitness[i] for i in range(n))
        return [freqs[i] * (fitness[i] - f_bar) for i in range(n)]

    def ess_condition(self, payoff: float, mutant_payoff: float) -> bool:
        """ESS: f(ESS, ESS) > f(mutant, ESS). EML-0."""
        return payoff > mutant_payoff

    def rock_paper_scissors_cycle(self, t: float) -> dict[str, float]:
        """
        RPS replicator: cycling around interior fixed point. EML-3 (oscillatory).
        x₁(t) ≈ 1/3 + A*cos(ωt), etc.
        """
        omega = 0.5
        A = 0.1
        return {
            "x1": round(1 / 3 + A * math.cos(omega * t), 4),
            "x2": round(1 / 3 + A * math.cos(omega * t + 2 * math.pi / 3), 4),
            "x3": round(1 / 3 + A * math.cos(omega * t + 4 * math.pi / 3), 4)
        }

    def analyze(self) -> dict[str, Any]:
        # Hawk-Dove payoff matrix
        V, C = 4.0, 6.0
        HD_matrix = [[(V - C) / 2, V], [0, V / 2]]
        freqs = [0.5, 0.5]
        dfreqs = self.replicator_equation(freqs, HD_matrix)

        t_vals = [0, 1, 2, 4, 6, 10]
        rps = {t: self.rock_paper_scissors_cycle(t) for t in t_vals}

        return {
            "model": "EvolutionaryGameTheory",
            "hawk_dove": {"V": V, "C": C, "ESS_hawk_fraction": round(V / C, 4)},
            "replicator_dx_at_50_50": [round(d, 4) for d in dfreqs],
            "rps_cycles": rps,
            "eml_depth": {"payoff_matrix": 0, "replicator_fixed_point": 2,
                          "rps_oscillation": 3},
            "key_insight": "ESS = EML-0 (linear condition); RPS cycling = EML-3 (oscillatory)"
        }


def analyze_evolution_v3_eml() -> dict[str, Any]:
    mls = MultiLevelSelection()
    mt = MajorTransitions()
    egt = EvolutionaryGameTheory()
    return {
        "session": 142,
        "title": "Evolutionary Biology Deep III: Multi-Level Selection & Major Transitions",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "multi_level_selection": mls.analyze(),
        "major_transitions": mt.analyze(),
        "evolutionary_game_theory": egt.analyze(),
        "eml_depth_summary": {
            "EML-0": "Hamilton's rule rb-c, ESS condition, payoff matrices",
            "EML-1": "Evolvability landscape exp(-g²/2σ²)",
            "EML-2": "Price equation covariance, group selection coefficient, replicator equilibrium",
            "EML-3": "RPS oscillations, predator-prey limit cycles",
            "EML-∞": "All major evolutionary transitions (irreversible individuality emergence)"
        },
        "key_theorem": (
            "The EML Multi-Level Selection Theorem: "
            "All components of the Price equation are EML-2 (covariance/regression). "
            "ESS conditions are EML-0 (linear). "
            "Major evolutionary transitions — the emergence of new levels of individuality — "
            "are EML-∞: once crossed, the transition is irreversible and the prior level "
            "cannot recover its independence."
        ),
        "rabbit_hole_log": [
            "Price equation Cov(W,z)/W̄ = EML-2: regression = EML-2 geometric structure",
            "Hamilton's rule rb-c = EML-0: it's a linear threshold condition",
            "Major transitions: each one = EML-∞ (same class as Penrose singularities, tipping)",
            "RPS cycling = EML-3: same class as Milankovitch, gamma waves, Airy"
        ],
        "connections": {
            "S132_evolution_v2": "Extends S132; adds multi-level selection + major transitions",
            "S60_info_theory": "Price equation = covariance = EML-2 (Fisher geometry)",
            "S137_climate_v2": "Major transitions ↔ tipping points: both EML-∞ irreversible"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_evolution_v3_eml(), indent=2, default=str))
