"""
Session 188 — Cellular Automata Deep II: CA Universality Strata & Emergence Taxonomy

EML operator: eml(x,y) = exp(x) - ln(y)
Key theorem: CA universality classes map to EML strata with sharper resolution:
Rule class I (fixed point) = EML-0; class II (periodic) = EML-3;
class III (chaotic) = EML-2 (Lyapunov); class IV (complex/universal) = EML-∞.
Kolmogorov complexity of CA patterns: EML-0 (simple) to EML-∞ (universal).
Emergence: local rules = EML-0/1; global patterns = EML-2/3; universality = EML-∞.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class WolframClassStrataEML:
    """Wolfram's 4 CA classes re-mapped to EML strata with depth justification."""

    def class_i_fixed_point(self) -> dict[str, Any]:
        """
        Class I: all initial conditions → uniform fixed point.
        Attractor = single state: EML-0 (integer-valued invariant).
        Convergence rate: exp(-t/τ). EML-1.
        Information lost: Shannon entropy H → 0. EML-2 → 0.
        Example: Rule 0, Rule 255 (all cells die/survive).
        """
        tau = 2.0
        t_vals = [1, 2, 5, 10]
        convergence = {t: round(math.exp(-t / tau), 6) for t in t_vals}
        return {
            "attractor": "uniform_fixed_point",
            "eml_depth_attractor": 0,
            "eml_depth_convergence": 1,
            "convergence_exp": convergence,
            "entropy_limit": 0,
            "eml_depth_entropy_approach": 2,
            "examples": ["Rule 0", "Rule 255"],
            "note": "Attractor=EML-0; convergence=EML-1; entropy descent=EML-2"
        }

    def class_ii_periodic(self) -> dict[str, Any]:
        """
        Class II: periodic or stable structures (still lifes, blinkers).
        Period p: EML-0 (integer). Spatial pattern: EML-3 (oscillatory in time/space).
        Lyapunov exponent λ = 0 (neutrally stable). EML-0.
        Autocorrelation: C(τ) = cos(2πτ/p). EML-3.
        Example: Rule 4, Rule 8 (periodic stripes).
        """
        periods = [2, 4, 8]
        autocorr = {}
        for p in periods:
            autocorr[p] = {
                tau: round(math.cos(2 * math.pi * tau / p), 4)
                for tau in range(p + 1)
            }
        return {
            "attractor_type": "periodic_orbit",
            "eml_depth_period": 0,
            "eml_depth_pattern": 3,
            "lyapunov": 0,
            "eml_depth_lyapunov": 0,
            "autocorrelations": autocorr,
            "examples": ["Rule 4", "Rule 8", "Conway blinker"],
            "note": "Period=EML-0; pattern oscillation=EML-3; λ=0 (EML-0)"
        }

    def class_iii_chaotic(self) -> dict[str, Any]:
        """
        Class III: pseudo-random, chaotic patterns.
        Lyapunov exponent λ > 0: EML-2 (log of divergence rate).
        Spatial entropy H_s ≈ log(2) per cell: EML-2.
        Two-point correlation: exponential decay exp(-r/ξ). EML-1.
        Fractal dimension D: EML-2 (log ratio).
        Kolmogorov complexity K ≈ n bits (incompressible): EML-∞ (uncomputable in general).
        Example: Rule 30, Rule 45.
        """
        lambda_val = 0.69
        spatial_entropy = math.log(2)
        xi = 3.0
        r_vals = [1, 2, 5, 10]
        correlation = {r: round(math.exp(-r / xi), 6) for r in r_vals}
        fractal_dim = 1 + math.log(1.5) / math.log(2)
        return {
            "lyapunov_exponent": round(lambda_val, 4),
            "eml_depth_lyapunov": 2,
            "spatial_entropy": round(spatial_entropy, 4),
            "eml_depth_entropy": 2,
            "correlation_length_xi": xi,
            "two_point_correlation": correlation,
            "eml_depth_correlation": 1,
            "fractal_dim": round(fractal_dim, 4),
            "eml_depth_fractal": 2,
            "kolmogorov_complexity": "∞ (uncomputable)",
            "eml_depth_kolmogorov": "∞",
            "examples": ["Rule 30", "Rule 45"],
            "note": "Chaos: λ=EML-2; entropy=EML-2; correlation=EML-1; K-complexity=EML-∞"
        }

    def class_iv_universal(self) -> dict[str, Any]:
        """
        Class IV: complex, universal computation.
        Halting problem for CA: EML-∞ (undecidable by Rice's theorem).
        Universal CA (Rule 110, GoL): simulation depth = EML-∞.
        Garden of Eden (no predecessor): existence proof = EML-∞.
        Finite pattern complexity: EML-3 (gliders, spaceships).
        Universal computation emergence: EML-∞.
        """
        return {
            "attractor_type": "complex_universal",
            "halting_problem": "undecidable",
            "eml_depth_halting": "∞",
            "eml_depth_simulation": "∞",
            "eml_depth_glider_pattern": 3,
            "garden_of_eden": "EML-∞ (existence undecidable for general CA)",
            "examples": ["Rule 110", "Conway's Game of Life"],
            "universal_computation": True,
            "eml_depth_universality": "∞",
            "note": "Universality=EML-∞; finite glider=EML-3; halting=EML-∞ (undecidable)"
        }

    def analyze(self) -> dict[str, Any]:
        c1 = self.class_i_fixed_point()
        c2 = self.class_ii_periodic()
        c3 = self.class_iii_chaotic()
        c4 = self.class_iv_universal()
        return {
            "model": "WolframClassStrataEML",
            "class_I": c1,
            "class_II": c2,
            "class_III": c3,
            "class_IV": c4,
            "eml_depth_map": {
                "class_I_attractor": 0, "class_I_convergence": 1,
                "class_II_period": 0, "class_II_pattern": 3,
                "class_III_lyapunov": 2, "class_III_correlation": 1,
                "class_IV_glider": 3, "class_IV_universal": "∞"
            },
            "key_insight": "CA classes: I=EML-0/1, II=EML-0/3, III=EML-2, IV=EML-3/∞"
        }


@dataclass
class EmergenceTaxonomyEML:
    """Emergence taxonomy: weak, strong, and radical, mapped to EML strata."""

    def weak_emergence(self, n_cells: int = 100) -> dict[str, Any]:
        """
        Weak emergence: macro properties computable from micro rules.
        Density ρ = (# live cells) / n: EML-0 (ratio).
        Mean field: ρ_{t+1} = f(ρ_t). EML-1 (logistic map = EML-1 approximation).
        Susceptibility χ = dρ/dp at phase transition: EML-∞.
        Correlation length ξ = exp(c/|p-p_c|^ν): EML-1 near transition.
        Weak emergence: macro = EML-2 (observable from micro by EML-2 coarse-graining).
        """
        p_vals = [0.3, 0.5, 0.593, 0.7]
        p_c = 0.593
        nu = 1.0
        results = {}
        for p in p_vals:
            dp = abs(p - p_c)
            if dp > 0.001:
                xi = math.exp(1.0 / (dp ** nu))
                eml = 1
            else:
                xi = float('inf')
                eml = "∞"
            results[round(p, 3)] = {
                "density": round(p, 3),
                "xi": round(xi, 2) if isinstance(xi, float) and xi < 1e6 else "∞",
                "eml_depth": eml
            }
        return {
            "n_cells": n_cells,
            "percolation_threshold": p_c,
            "density_depth": 0,
            "mean_field_depth": 1,
            "correlation_length_results": results,
            "eml_depth_transition": "∞",
            "weak_emergence_depth": 2,
            "note": "Weak emergence: macro computable by EML-2 coarse-graining; transition=EML-∞"
        }

    def strong_emergence(self) -> dict[str, Any]:
        """
        Strong emergence: macro properties NOT deducible from micro.
        Consciousness: EML-∞ (explanatory gap).
        Life (GoL): pattern complexity irreducible without simulation. EML-∞.
        Effective complexity E(x) = K(x) - K(random): EML-∞ (K uncomputable).
        Logical depth: Bennett's LD(x) = min time to compute x. EML-∞ (Turing machine time).
        Strong emergence: macro = EML-∞ w.r.t. micro description.
        """
        return {
            "consciousness_depth": "∞",
            "life_complexity_depth": "∞",
            "kolmogorov_depth": "∞",
            "logical_depth": "∞",
            "effective_complexity": "∞ (uncomputable)",
            "eml_depth_strong_emergence": "∞",
            "eml_depth_micro_rules": 0,
            "asymmetry": "micro=EML-0; strong macro=EML-∞; Δd=∞",
            "note": "Strong emergence: cannot be deduced from micro by any EML-finite procedure"
        }

    def kolmogorov_complexity_strata(self, n: int = 100) -> dict[str, Any]:
        """
        Kolmogorov complexity K(x) for various CA outputs:
        Uniform output: K = O(log n). EML-0 (description length grows log).
        Periodic output: K = O(log n + log period). EML-0.
        Rule 30 output: K ≈ n (incompressible). EML-∞ (uncomputable).
        Universal CA output: K(x) ≈ K(program) = constant. EML-∞.
        Compressibility = (n - K(x))/n: EML-0 (uniform) to EML-∞ (random).
        """
        uniform_k = math.log2(n)
        periodic_k = math.log2(n) + math.log2(4)
        return {
            "n": n,
            "uniform_K": round(uniform_k, 2),
            "eml_depth_uniform": 0,
            "periodic_K": round(periodic_k, 2),
            "eml_depth_periodic": 0,
            "chaotic_K_approx": n,
            "eml_depth_chaotic": "∞",
            "universal_K": "constant (program size)",
            "eml_depth_universal": "∞",
            "note": "K-complexity: simple→EML-0; random→EML-∞; universal→EML-∞"
        }

    def analyze(self) -> dict[str, Any]:
        weak = self.weak_emergence()
        strong = self.strong_emergence()
        kolm = self.kolmogorov_complexity_strata()
        return {
            "model": "EmergenceTaxonomyEML",
            "weak_emergence": weak,
            "strong_emergence": strong,
            "kolmogorov_strata": kolm,
            "eml_depth": {
                "micro_rules": 0, "density": 0,
                "mean_field": 1, "correlation": 1,
                "coarse_grain": 2, "phase_transition": "∞",
                "strong_emergence": "∞", "kolmogorov": "∞"
            },
            "key_insight": "Weak=EML-2 (computable coarse-grain); strong=EML-∞ (non-deducible)"
        }


@dataclass
class UniversalityDepthEML:
    """CA universality: simulation, Rice's theorem, and depth asymmetry."""

    def simulation_depth(self) -> dict[str, Any]:
        """
        CA simulation hierarchy:
        CA simulates finite automaton: EML-0 (bounded lookup).
        CA simulates pushdown automaton: EML-1 (stack depth = exp growth).
        CA simulates Turing machine: EML-∞ (undecidable properties).
        Universal CA simulates any CA: EML-∞.
        Depth of simulation = depth of simulated object.
        """
        return {
            "finite_automaton": {"depth": 0, "reason": "bounded lookup, EML-0 transition"},
            "pushdown_automaton": {"depth": 1, "reason": "stack ~ exp(n) depth, EML-1"},
            "turing_machine": {"depth": "∞", "reason": "halting undecidable, Rice's theorem"},
            "universal_ca": {"depth": "∞", "reason": "simulates all TMs, EML-∞"},
            "eml_asymmetry": "simulating (EML-∞) vs being simulated (EML-finite): Δd=∞",
            "note": "Simulation ladder: FA=EML-0, PDA=EML-1, TM=EML-∞"
        }

    def rice_theorem_eml(self) -> dict[str, Any]:
        """
        Rice's theorem: any non-trivial semantic property of programs (CAs) is undecidable.
        Halting: undecidable = EML-∞.
        Syntactic properties (rule number): decidable = EML-0.
        Semantic properties (does CA halt, produce pattern, reach fixed point?): EML-∞.
        The syntax/semantics gap = EML-0 vs EML-∞ = maximal asymmetry.
        """
        return {
            "syntactic_properties": {
                "rule_number": {"decidable": True, "depth": 0},
                "neighborhood_size": {"decidable": True, "depth": 0},
                "state_count": {"decidable": True, "depth": 0}
            },
            "semantic_properties": {
                "halting": {"decidable": False, "depth": "∞"},
                "fixed_point_existence": {"decidable": False, "depth": "∞"},
                "pattern_production": {"decidable": False, "depth": "∞"},
                "universality": {"decidable": False, "depth": "∞"}
            },
            "syntax_depth": 0,
            "semantics_depth": "∞",
            "delta_d": "∞",
            "note": "Syntax=EML-0; semantics=EML-∞: Rice's theorem = maximal Asymmetry Theorem instance"
        }

    def garden_of_eden_eml(self) -> dict[str, Any]:
        """
        Garden of Eden (GoE): configurations with no predecessor.
        Moore-Myhill theorem: GoE iff injective.
        Injectivity check: EML-0 (algebraic, computable for finite CA).
        GoE existence: EML-0 for finite CA (decidable, constructive).
        GoE for infinite CA: EML-∞ (undecidable in general).
        Finding a specific GoE: EML-∞ (search space = 2^n).
        """
        return {
            "moore_myhill_depth": 0,
            "injectivity_depth": 0,
            "goe_existence_finite_depth": 0,
            "goe_existence_infinite_depth": "∞",
            "goe_search_depth": "∞",
            "eml_asymmetry": "existence check=EML-0; finding one=EML-∞: Δd=∞",
            "note": "GoE: decidability=EML-0; construction=EML-∞; Asymmetry Theorem applies"
        }

    def analyze(self) -> dict[str, Any]:
        sim = self.simulation_depth()
        rice = self.rice_theorem_eml()
        goe = self.garden_of_eden_eml()
        return {
            "model": "UniversalityDepthEML",
            "simulation_hierarchy": sim,
            "rice_theorem": rice,
            "garden_of_eden": goe,
            "eml_depth": {
                "syntax": 0, "decidable_properties": 0,
                "pushdown": 1, "semantics": "∞",
                "universality": "∞", "goe_existence": 0, "goe_construction": "∞"
            },
            "key_insight": "Rice=maximal Asymmetry: syntax=EML-0, semantics=EML-∞, Δd=∞"
        }


def analyze_automata_v3_eml() -> dict[str, Any]:
    wolfram = WolframClassStrataEML()
    emergence = EmergenceTaxonomyEML()
    universality = UniversalityDepthEML()
    return {
        "session": 188,
        "title": "Cellular Automata Deep II: CA Universality Strata & Emergence Taxonomy",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "wolfram_classes": wolfram.analyze(),
        "emergence_taxonomy": emergence.analyze(),
        "universality_depth": universality.analyze(),
        "eml_depth_summary": {
            "EML-0": "Class I attractor, period, Lyapunov=0, rule syntax, GoE existence (finite), density",
            "EML-1": "Convergence exp(-t/τ), mean field, correlation decay, PDA stack depth",
            "EML-2": "Lyapunov exponent (Class III), spatial entropy, fractal dimension, coarse-graining",
            "EML-3": "Class II pattern oscillation, gliders/spaceships in Class IV",
            "EML-∞": "Class IV universality, halting, Rice's theorem, Kolmogorov complexity, strong emergence"
        },
        "key_theorem": (
            "The EML CA Universality Strata Theorem: "
            "Wolfram's four CA classes map precisely to EML depth strata: "
            "Class I (fixed point) = EML-0/EML-1 (attractor + convergence). "
            "Class II (periodic) = EML-0/EML-3 (period + oscillation). "
            "Class III (chaotic) = EML-2 (Lyapunov, entropy, fractal dimension). "
            "Class IV (universal) = EML-3/EML-∞ (finite patterns + universality). "
            "Rice's theorem is the maximal Asymmetry Theorem instance: "
            "syntax (EML-0) vs semantics (EML-∞), Δd=∞. "
            "Emergence taxonomy: weak = EML-2 (computable coarse-grain); "
            "strong = EML-∞ (non-deducible from micro). "
            "The Asymmetry Theorem applies to Garden of Eden: "
            "existence check = EML-0; construction = EML-∞; Δd=∞. "
            "Kolmogorov complexity: uniform/periodic = EML-0; random/universal = EML-∞."
        ),
        "rabbit_hole_log": [
            "Class III = EML-2 (Lyapunov): same stratum as Fisher info, running coupling — universal EML-2",
            "Rice's theorem = maximal Asymmetry Theorem: syntax=EML-0, semantics=EML-∞, Δd=∞",
            "GoE: existence=EML-0, construction=EML-∞: another Δd=∞ pair from Asymmetry Theorem",
            "Weak emergence = EML-2: coarse-graining preserves depth (same as EML-2 skeleton theorem)",
            "Strong emergence = EML-∞: same depth as consciousness, confinement proof, path integrals",
            "PDA simulation = EML-1: stack depth grows exponentially — universal EML-1 again"
        ],
        "connections": {
            "S178_automata": "S178: Class IV=EML-∞, Rule 30=EML-3; S188 adds emergence taxonomy + Rice",
            "S111_asym": "Rice's theorem = strongest Asymmetry instance: Δd=∞ between syntax and semantics",
            "S184_cognition": "Strong emergence = EML-∞ = qualia: same depth as explanatory gap"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_automata_v3_eml(), indent=2, default=str))
