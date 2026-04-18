"""
Session 112 — Extreme Value Theory & Rare Events: EML of Extremes

Gumbel, Fréchet, Weibull, GEV, and the Fisher-Tippett-Gnedenko theorem.
What is the EML depth of the most extreme outcomes?

Key theorem: All three extreme value attractors (Gumbel, Fréchet, Weibull)
are EML-2. Gumbel exp(-exp(-x)) is EML-1∘EML-1 = EML-2 (double exp).
Fréchet exp(-x^{-α}) is EML-1∘EML-2 = EML-2. Black swans are EML-2 tails
miscalibrated, not EML-∞. True EML-∞ rare events: Lévy stable non-Gaussian.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field


EML_INF = float("inf")


@dataclass
class ExtremeValueDistributions:
    """
    The three extreme value attractors (Fisher-Tippett-Gnedenko theorem).

    All maxima of i.i.d. sequences converge to one of three types:
    - Type I  (Gumbel):  F(x) = exp(-exp(-x)): EML-2 (double exponential)
    - Type II (Fréchet): F(x) = exp(-x^{-α}) for x>0: EML-2 (exp of power law)
    - Type III (Weibull): F(x) = exp(-(-x)^α) for x<0: EML-2

    Unification: GEV F(x) = exp(-(1+ξ·x)^{-1/ξ}) for ξ≠0; Gumbel for ξ=0.
    All EML-2. The extremes of random variables are EML-2.
    """

    def gumbel_cdf(self, x: float, mu: float = 0.0, beta: float = 1.0) -> dict:
        """F(x) = exp(-exp(-(x-μ)/β)): double exponential."""
        z = (x - mu) / beta
        F = math.exp(-math.exp(-z))
        f = math.exp(-z - math.exp(-z)) / beta
        return {
            "x": x, "mu": mu, "beta": beta,
            "F_x": round(F, 6),
            "f_x": round(f, 6),
            "eml": 2,
            "reason": "F = exp(-exp(-z)): EML-1∘EML-1 = EML-2 (double exponential)",
        }

    def frechet_cdf(self, x: float, alpha: float = 2.0, mu: float = 0.0,
                    sigma: float = 1.0) -> dict:
        """F(x) = exp(-((x-μ)/σ)^{-α}) for x > μ."""
        if x <= mu:
            return {"x": x, "F_x": 0.0, "eml": 2}
        z = (x - mu) / sigma
        F = math.exp(-(z ** (-alpha)))
        f = (alpha / sigma) * z ** (-alpha - 1) * F
        return {
            "x": x, "alpha": alpha,
            "F_x": round(F, 6),
            "f_x": round(f, 6),
            "eml": 2,
            "reason": "F = exp(-x^{-α}): EML-1∘EML-2(power law) = EML-2",
        }

    def weibull_cdf(self, x: float, alpha: float = 2.0, mu: float = 0.0,
                    sigma: float = 1.0) -> dict:
        """F(x) = exp(-(-(x-μ)/σ)^α) for x < μ (reversed Weibull for maxima)."""
        if x >= mu:
            return {"x": x, "F_x": 1.0, "eml": 2}
        z = -(x - mu) / sigma
        F = math.exp(-(z ** alpha))
        return {
            "x": x, "alpha": alpha,
            "F_x": round(F, 6),
            "eml": 2,
            "reason": "F = exp(-(-x/σ)^α): EML-2 (exp of power law of reflected variable)",
        }

    def gev_cdf(self, x: float, xi: float, mu: float = 0.0,
                sigma: float = 1.0) -> dict:
        """Generalized Extreme Value: F(x) = exp(-(1+ξ(x-μ)/σ)^{-1/ξ})."""
        z = (x - mu) / sigma
        arg = 1 + xi * z
        if arg <= 0:
            F = 0.0 if xi > 0 else 1.0
        elif abs(xi) < 1e-6:
            F = math.exp(-math.exp(-z))
        else:
            F = math.exp(-arg ** (-1 / xi))
        family = "Fréchet" if xi > 0 else "Weibull" if xi < 0 else "Gumbel"
        return {
            "x": x, "xi": xi, "mu": mu, "sigma": sigma,
            "F_x": round(F, 6),
            "family": family,
            "eml": 2,
            "reason": "GEV unification: all three types = EML-2",
        }

    def to_dict(self) -> dict:
        x_vals = [-2, -1, 0, 1, 2, 3, 4]
        return {
            "gumbel": [self.gumbel_cdf(x) for x in x_vals],
            "frechet_alpha2": [self.frechet_cdf(x, 2.0) for x in [0.5, 1.0, 2.0, 5.0, 10.0]],
            "weibull_alpha2": [self.weibull_cdf(x, 2.0) for x in [-3.0, -2.0, -1.0, -0.5, 0.0]],
            "gev_family": [
                self.gev_cdf(2.0, xi=xi) for xi in [-0.5, -0.1, 0.0, 0.1, 0.5]
            ],
            "eml_gumbel": 2,
            "eml_frechet": 2,
            "eml_weibull": 2,
            "eml_gev": 2,
            "fisher_tippett_gnedenko": "All extreme value attractors are EML-2 (double exponential or exp of power law)",
        }


@dataclass
class ReturnPeriods:
    """
    Return period and quantile estimation for extreme events.

    EML structure:
    - Return level x_T (event exceeded once per T years):
      For Gumbel: x_T = μ - β·ln(-ln(1-1/T)): EML-2 (ln of ln = double log)
      For Fréchet: x_T = μ + σ·(-ln(1-1/T))^{-1/α}: EML-2
    - Empirical return period: T_i = (n+1)/i (Weibull plotting): EML-0 (rational)
    - Tail probability extrapolation: EML-2 (log-linear in return period)
    - 100-year flood: not EML-∞ — it's an EML-2 quantile estimate
    - Black swan threshold: EML-2 (we just didn't measure long enough)
    """

    def gumbel_return_level(self, T: float, mu: float = 0.0,
                             beta: float = 1.0) -> dict:
        """x_T = μ - β·ln(-ln(1-1/T)) for Gumbel."""
        if T <= 1:
            return {"T": T, "x_T": mu, "eml": 2}
        p = 1 - 1.0 / T
        x_T = mu - beta * math.log(-math.log(p))
        return {
            "T_years": T,
            "x_T": round(x_T, 4),
            "exceedance_prob": round(1 / T, 6),
            "eml": 2,
            "reason": "x_T = μ - β·ln(-ln(1-1/T)): EML-2 (ln of ln = double logarithm)",
        }

    def frechet_return_level(self, T: float, alpha: float = 2.0,
                              sigma: float = 1.0) -> dict:
        """x_T = σ·(-ln(1-1/T))^{-1/α} for Fréchet."""
        if T <= 1:
            return {"T": T, "x_T": sigma, "eml": 2}
        p = 1 - 1.0 / T
        x_T = sigma * (-math.log(p)) ** (-1.0 / alpha)
        return {
            "T_years": T,
            "x_T": round(x_T, 4),
            "eml": 2,
            "reason": "x_T = σ·(-ln p)^{-1/α}: EML-2 (power of logarithm)",
        }

    def black_swan_analysis(self) -> dict:
        return {
            "claim": "Black swans are EML-2, not EML-∞",
            "argument": (
                "Taleb's 'black swans' are events in the tails of Fréchet distributions (power law tails). "
                "P(X > x) ~ x^{-α}: this is EML-2 (power law). "
                "The surprise is not that the distribution is EML-∞, but that we fitted "
                "a thin-tailed EML-3 Gaussian to an EML-2 power-law process. "
                "Black swans = EML-2 events modeled as if EML-3 → apparent EML-∞ surprise."
            ),
            "true_eml_inf_rare": (
                "Lévy stable distributions with index α<2 and no closed form (except Gaussian α=2, "
                "Cauchy α=1, Lévy α=1/2): these are EML-∞ (no elementary closed form). "
                "Genuinely EML-∞ rare events have no computable return period."
            ),
            "eml_model_mismatch": "EML-3 model on EML-2 data = apparent EML-∞ surprise",
        }

    def to_dict(self) -> dict:
        T_vals = [2, 5, 10, 25, 50, 100, 500, 1000]
        return {
            "gumbel_return_levels": [self.gumbel_return_level(T) for T in T_vals],
            "frechet_return_levels": [self.frechet_return_level(T) for T in T_vals],
            "black_swan": self.black_swan_analysis(),
        }


@dataclass
class RecordStatistics:
    """
    Record values: the k-th record in an i.i.d. sequence.

    EML structure:
    - Expected number of records in n trials: H_n = Σ_{k=1}^n 1/k ≈ ln(n): EML-2
    - Inter-record waiting time: E[Δ_k] = k: EML-0 (arithmetic mean = EML-0 rational)
    - Record increments (Gumbel): Δ_k ~ Exponential(1): EML-1 (exponential distribution)
    - Record maximum after n: E[max] ≈ μ + β·ln(n): EML-2 (logarithm of n)
    - Record times T_k: log-normally distributed ~ EML-2 (Gaussian on log scale)
    """

    def expected_records(self, n: int) -> dict:
        H_n = sum(1.0 / k for k in range(1, n + 1))
        return {
            "n": n,
            "E_records": round(H_n, 4),
            "approx_ln_n": round(math.log(n), 4),
            "eml": 2,
            "reason": "E[records] = H_n ≈ ln(n): EML-2 (harmonic number → logarithm)",
        }

    def record_maximum_expectation(self, n: int, mu: float = 0.0,
                                    beta: float = 1.0) -> dict:
        E_max = mu + beta * math.log(n)
        return {
            "n": n, "mu": mu, "beta": beta,
            "E_max": round(E_max, 4),
            "eml": 2,
            "reason": "E[max] ≈ μ + β·ln(n): EML-2 (logarithmic growth of expected maximum)",
        }

    def to_dict(self) -> dict:
        return {
            "expected_records": [self.expected_records(n) for n in [10, 100, 1000, 10000]],
            "record_maxima": [self.record_maximum_expectation(n) for n in [10, 100, 1000, 10000]],
            "record_increment_eml": 1,
            "record_waiting_time_eml": 0,
            "log_normal_record_times_eml": 2,
        }


def analyze_evt_eml() -> dict:
    evd = ExtremeValueDistributions()
    ret = ReturnPeriods()
    rec = RecordStatistics()
    return {
        "session": 112,
        "title": "Extreme Value Theory & Rare Events: EML of Extremes",
        "key_theorem": {
            "theorem": "EML Extreme Value Theorem",
            "statement": (
                "All three extreme value attractors are EML-2: "
                "Gumbel F(x)=exp(-exp(-x)) is EML-2 (double exponential = EML-1∘EML-1). "
                "Fréchet F(x)=exp(-x^{-α}) is EML-2 (exp of power law). "
                "Weibull F(x)=exp(-(-x)^α) is EML-2. "
                "GEV unification is EML-2. "
                "Return levels x_T = EML-2 (ln of ln for Gumbel). "
                "Expected records H_n ≈ ln(n) = EML-2. "
                "Black swans are EML-2 Fréchet tails mislabeled as EML-∞. "
                "True EML-∞ rare events: Lévy stable (no closed form)."
            ),
        },
        "extreme_value_distributions": evd.to_dict(),
        "return_periods": ret.to_dict(),
        "record_statistics": rec.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Return period counting (n+1)/i; inter-record waiting time E[Δ_k]=k",
            "EML-1": "Record increments ~ Exp(1); Gumbel inner layer exp(-z)",
            "EML-2": "All EVT attractors (Gumbel/Fréchet/Weibull/GEV); return levels ln(-ln(p)); E[records]≈ln(n)",
            "EML-3": "Not present naturally in EVT (no oscillation)",
            "EML-∞": "Lévy stable (no closed form except Gaussian/Cauchy/Lévy); true model uncertainty",
        },
        "rabbit_hole_log": [
            "The double exponential is EML-2, not EML-3: Gumbel F(x)=exp(-exp(-x)) looks like it should be deep, but it's EML-1∘EML-1 = EML-2 by the composition law. This is surprising — the distribution of maximum values is simpler (EML-2) than the distribution of individual values might be (EML-3 for Gaussian). Extremes are simpler than typical values!",
            "Return levels are double-logarithmic (EML-2): the 100-year flood level x_{100} = μ - β·ln(-ln(0.99)) ≈ μ + β·4.6. The formula involves ln(ln(T)) — two nested logarithms = EML-2. Every civil engineer computing flood levels is doing EML-2 arithmetic.",
            "Black swans are an EML model mismatch: Taleb's insight is correct empirically but mislabeled mathematically. The 'black swan' phenomenon is EML-2 (power law) presented as if EML-3 (Gaussian). The surprise is from applying the wrong EML depth model. The events themselves are EML-2 — just the model was wrong.",
            "Records grow logarithmically (EML-2): after 1 million trials, you expect only ~14 records (ln(10⁶) ≈ 13.8). Records are rare not because of EML-∞ complexity but because of EML-2 logarithmic scarcity. The rarity of records is the rarity of EML-2 events at the tail.",
        ],
        "connections": {
            "to_session_95": "Finance fat tails = EML-2 (confirmed). EVT Fréchet is the precise distribution behind power-law tails.",
            "to_session_111": "Gumbel = EML-1∘EML-1 = EML-2 by composition law from S111. EVT confirms the depth arithmetic.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_evt_eml(), indent=2, default=str))
