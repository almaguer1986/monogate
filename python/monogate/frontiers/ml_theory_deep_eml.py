"""
Session 96 — ML Theory Deep: Grokking, Emergence & Scaling Laws

Grokking (sudden generalization), phase transitions during training, double descent,
emergent abilities, and neural scaling laws through the EML depth lens.

Key hypothesis: Grokking corresponds to a learned representation dropping from EML-∞
(memorization = random lookup table) to EML-3 (generalization = structured oscillation/
modular arithmetic). Neural scaling laws (loss ~ N^{-α}) are EML-2 (power law).
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field


EML_INF = float("inf")


@dataclass
class GrokkingEML:
    """
    Grokking (Power et al. 2022): training on modular arithmetic.
    Models first memorize (100% train acc, ~0% test acc), then after many more steps
    suddenly generalize (100% test acc).

    EML depth interpretation:
    - Phase 1 (memorization): model = lookup table = EML-∞ (no structure, just key-value)
    - Phase 2 (grokking): model discovers Fourier features = EML-3 (sin/cos of modular freq)
    - The grokking transition: EML-∞ → EML-3 depth drop (a depth reduction!)
    - Grokking delay ~ regularization strength: longer delay = harder EML depth drop
    - Weight norm before grokking: large (EML-∞ regime); after: small (EML-3 efficient)
    """

    def modular_addition_fourier(self, p: int = 97) -> dict:
        """
        (a+b) mod p: Fourier features ω_k(a) = exp(2πi·k·a/p) are EML-3.
        The learned solution uses O(1) Fourier modes: EML-3 finite sum.
        Memorization requires p² parameters: EML-∞ lookup.
        """
        n_train_pairs = p * p
        n_fourier_modes = min(p, 20)  # sparse Fourier: only a few modes needed
        return {
            "modulus_p": p,
            "n_training_pairs": n_train_pairs,
            "memorization_parameters": n_train_pairs,
            "generalization_fourier_modes": n_fourier_modes,
            "compression_ratio": round(n_train_pairs / n_fourier_modes, 2),
            "eml_memorization": EML_INF,
            "eml_generalization": 3,
            "fourier_features": "ω_k(a) = exp(2πi·k·a/p): EML-3",
            "grokking_transition": "EML-∞ (lookup table) → EML-3 (Fourier) during training",
        }

    def grokking_loss_curve(self) -> list[dict]:
        """Synthetic: loss ~ L_0·exp(-t/τ_gen) after grokking epoch t_grok."""
        t_grok = 500
        L_mem = 0.0  # train
        results = []
        for t in [100, 300, 500, 700, 1000, 1500, 2000]:
            train_loss = 0.0
            if t < t_grok:
                test_loss = 2.3  # random chance for 10 classes ~ -log(0.1)
                test_acc = 0.1
                eml = EML_INF
            else:
                test_loss = 2.3 * math.exp(-(t - t_grok) / 300)
                test_acc = 1 - math.exp(-(t - t_grok) / 300)
                eml = 3
            results.append({
                "epoch": t,
                "train_loss": train_loss,
                "test_loss": round(test_loss, 4),
                "test_accuracy": round(test_acc, 4),
                "eml_representation": "∞" if eml == EML_INF else eml,
            })
        return results

    def to_dict(self) -> dict:
        return {
            "phenomenon": "Grokking: delayed generalization in modular arithmetic",
            "modular_fourier": self.modular_addition_fourier(97),
            "loss_curve": self.grokking_loss_curve(),
            "eml_interpretation": "Grokking = EML-∞ → EML-3 transition: model drops from memorization (EML-∞) to Fourier generalization (EML-3)",
            "weight_norm_proxy": "Weight norm decrease tracks EML depth reduction during grokking",
        }


@dataclass
class NeuralScalingLaws:
    """
    Chinchilla scaling law: L(N,D) = E + A/N^α + B/D^β
    where N = model size, D = data size.

    EML structure:
    - L(N): power law in N → EML-2 (power = exp(α·ln N))
    - Optimal allocation: N* ~ D/20 (Chinchilla): EML-0 (linear, integer coefficient)
    - Emergent abilities: tasks where L_task drops abruptly at threshold N_c → EML-∞
    - Irreducible entropy E: EML-0 (constant lower bound)
    - Exponents α, β ≈ 0.3-0.5: EML-2 (rational powers)
    """

    E: float = 1.69  # irreducible entropy (nats, Chinchilla)
    A: float = 406.4
    alpha: float = 0.34
    B: float = 410.7
    beta: float = 0.28

    def loss(self, N: float, D: float) -> dict:
        loss = self.E + self.A / N**self.alpha + self.B / D**self.beta
        return {
            "N_params": N,
            "D_tokens": D,
            "loss": round(loss, 6),
            "eml_loss_fn": 2,
            "reason": "L = E + A/N^α + B/D^β: power laws in N,D = EML-2",
        }

    def optimal_allocation(self, C: float) -> dict:
        """Given compute C (FLOPs), find optimal N* and D*: N* ∝ C^{0.5}, D* ∝ C^{0.5}."""
        N_star = (C / 6)**(0.5 * self.alpha / (self.alpha + self.beta))
        D_star = C / (6 * N_star)
        return {
            "compute_C": C,
            "N_star": round(N_star, 2),
            "D_star": round(D_star, 2),
            "eml": 2,
            "reason": "N* ~ C^{exponent}: power law in compute = EML-2",
        }

    def emergent_abilities(self) -> list[dict]:
        return [
            {
                "ability": "Multi-digit arithmetic",
                "threshold_approx_B_params": 6,
                "eml_below": EML_INF,
                "eml_above": 3,
                "description": "Below threshold: random guessing = EML-∞; above: algorithmic computation = EML-3",
            },
            {
                "ability": "Chain-of-thought reasoning",
                "threshold_approx_B_params": 100,
                "eml_below": EML_INF,
                "eml_above": 3,
                "description": "Below: incoherent chains = EML-∞; above: structured steps = EML-3",
            },
            {
                "ability": "In-context learning (few-shot)",
                "threshold_approx_B_params": 1,
                "eml_below": EML_INF,
                "eml_above": 2,
                "description": "Below: ignores context = EML-∞; above: linear extrapolation = EML-2",
            },
        ]

    def to_dict(self) -> dict:
        compute_vals = [1e18, 1e20, 1e22, 1e24]
        N_vals = [1e8, 1e9, 1e10, 1e11]
        D_val = 1e12
        return {
            "scaling_law": "L(N,D) = E + A/N^α + B/D^β (Chinchilla)",
            "loss_vs_N": [self.loss(N, D_val) for N in N_vals],
            "optimal_allocation": [self.optimal_allocation(C) for C in compute_vals[:3]],
            "emergent_abilities": self.emergent_abilities(),
            "eml_loss": 2,
            "eml_irreducible": 0,
            "eml_emergent_transition": EML_INF,
        }


@dataclass
class DoubleDescent:
    """
    Double descent: bias-variance tradeoff has a second descent phase for overparameterized models.

    Classical regime (N < n_data): L ~ (n_data-N)^{-1}: EML-2 (rational power)
    Interpolation threshold N = n_data: L → ∞: EML-∞ (blowup at threshold)
    Overparameterized (N > n_data): L decreases again: EML-2 (power law)

    EML structure:
    - Classical bias term: O(1/N) decay: EML-2
    - Variance at interpolation threshold: EML-∞ (diverges)
    - Overparameterized bias: EML-2 (implicit regularization from SGD)
    """

    def risk_curve(self, n_data: int = 100) -> list[dict]:
        results = []
        for N in [20, 50, 80, 95, 100, 105, 120, 150, 200, 500]:
            if N < n_data:
                risk = 1.0 / (1 - N/n_data) if N < n_data * 0.99 else 100.0
                regime = "classical"
                eml = 2
            elif N == n_data:
                risk = float("inf")
                regime = "interpolation"
                eml = EML_INF
            else:
                risk = n_data / N  # implicit regularization: benign overfitting
                regime = "overparameterized"
                eml = 2
            results.append({
                "N_params": N,
                "risk": round(risk, 4) if risk < 1e6 else "∞",
                "regime": regime,
                "eml": "∞" if eml == EML_INF else eml,
            })
        return results

    def to_dict(self) -> dict:
        return {
            "phenomenon": "Double descent: risk curve has two humps",
            "risk_curve": self.risk_curve(100),
            "eml_classical": 2,
            "eml_threshold": EML_INF,
            "eml_overparameterized": 2,
            "insight": "Double descent: the interpolation threshold is EML-∞ (divergence), flanked by EML-2 regions. Same structure as a phase transition (EML-∞ at critical point, EML-2 away).",
        }


def analyze_ml_theory_deep_eml() -> dict:
    grok = GrokkingEML()
    scaling = NeuralScalingLaws()
    descent = DoubleDescent()
    return {
        "session": 96,
        "title": "ML Theory Deep: Grokking, Emergence & Scaling Laws",
        "key_theorem": {
            "theorem": "EML ML Phase Transition Theorem",
            "statement": (
                "Grokking is an EML-∞ → EML-3 transition: memorization (EML-∞ lookup table) "
                "gives way to Fourier generalization (EML-3 modular features). "
                "Scaling laws L ~ N^{-α} are EML-2 (power law). "
                "Emergent abilities are EML-∞ → EML-3 sharp transitions at threshold compute. "
                "Double descent has EML-∞ at the interpolation threshold flanked by EML-2. "
                "These are all instances of the EML Phase Transition Theorem from Session 57: "
                "non-analytic events = EML-∞; smooth learning dynamics = EML-2."
            ),
        },
        "grokking": grok.to_dict(),
        "neural_scaling_laws": scaling.to_dict(),
        "double_descent": descent.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Irreducible entropy E; integer token counts; discrete labels",
            "EML-1": "Gradient descent loss decay exp(-t/τ) (exponential convergence near minimum)",
            "EML-2": "Scaling law L~N^{-α}; optimal compute allocation; GARCH-like ACF of training loss; VaR of test loss",
            "EML-3": "Generalized Fourier features (grokking solution); attention patterns (sinusoidal PE); emergent structured reasoning",
            "EML-∞": "Memorization regime; pre-emergence random guessing; interpolation threshold blowup",
        },
        "rabbit_hole_log": [
            "Grokking and the EML depth transition: the model weight norm decreases at grokking. In EML terms, a smaller, more structured weight corresponds to a shallower EML tree. The grokking transition is the model 'discovering' a depth-3 Fourier solution after trying depth-∞ memorization.",
            "Emergent abilities are the ML analog of phase transitions (Session 57). Before threshold: EML-∞ (random behavior). After: EML-3 (structured capability). The transition is sharp → EML-∞ intermediate state.",
            "Scaling law exponent α ≈ 0.3-0.5: these are in (0,1), suggesting EML-2 (power law) with a non-integer, non-simple exponent. Unlike physics exponents (e.g., ν=1/2 for mean field = rational), ML scaling exponents are EML-2 irrational-looking but empirically clean.",
        ],
        "connections": {
            "to_session_57": "Phase transitions = EML-∞. Grokking, emergence, double descent = EML-∞ transitions in ML",
            "to_session_84": "Wilson-Fisher: approach to fixed point = EML-1. Scaling law convergence to L=E = EML-1 asymptote",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_ml_theory_deep_eml(), indent=2, default=str))
