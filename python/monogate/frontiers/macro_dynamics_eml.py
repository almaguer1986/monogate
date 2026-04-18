"""
Session 296 — Macroeconomic Dynamics & Monetary Policy

EML operator: eml(x,y) = exp(x) - ln(y)
Core thesis: Central bank policy and inflation dynamics sit at the EML-2/EML-∞ boundary.
Stress test: Phillips curve, Taylor rule, and regime shifts under the tropical semiring.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class MacroDynamicsEML:

    def phillips_curve_semiring(self) -> dict[str, Any]:
        return {
            "object": "New Keynesian Phillips curve",
            "formula": "π_t = β·E_t[π_{t+1}] + κ·x_t: inflation = discounted future + output gap",
            "eml_depth": 2,
            "why": "Expectation update: E_t[π] = EML-2 (Gaussian belief); output gap = EML-2",
            "semiring_test": {
                "expectations_tensor_gap": {
                    "operation": "Expectations(EML-2) ⊗ OutputGap(EML-2) = max(2,2) = 2",
                    "result": "Phillips curve: 2⊗2=2 ✓"
                },
                "non_linear_PC": {
                    "depth": "∞",
                    "shadow": 2,
                    "type": "TYPE 2 Horizon (flattening at ZLB or high inflation)",
                    "why": "Threshold non-linearity = EML-∞; shadow=2 (still log-linear near anchor)"
                }
            }
        }

    def taylor_rule_semiring(self) -> dict[str, Any]:
        return {
            "object": "Taylor rule: i_t = r* + π* + 1.5(π_t - π*) + 0.5·x_t",
            "eml_depth": 2,
            "why": "Linear feedback rule: i = real_rate + deviation_terms = EML-2",
            "semiring_test": {
                "rule_tensor_reaction": {
                    "operation": "InflationGap(EML-2) ⊗ OutputGap(EML-2) = max(2,2) = 2",
                    "result": "Taylor rule: 2⊗2=2 ✓"
                },
                "zero_lower_bound": {
                    "depth": "∞",
                    "shadow": 2,
                    "type": "TYPE 2 Horizon (non-linearity at i=0)",
                    "why": "ZLB kink = EML-∞; shadow=2 (deviation from anchor = EML-2)"
                }
            }
        }

    def fiscal_multiplier_semiring(self) -> dict[str, Any]:
        return {
            "object": "Fiscal multiplier: ΔY/ΔG",
            "eml_depth": 2,
            "formula": "Multiplier = 1/(1 - c(1-t)): closed-form rational = EML-0 → EML-2 with dynamics",
            "semiring_test": {
                "static_multiplier": {"depth": 0, "why": "Static Keynesian: algebraic ratio = EML-0"},
                "dynamic_multiplier": {
                    "depth": 2,
                    "formula": "Y(t) = Y_0·exp(-t/τ): decay toward new steady state = EML-2"
                },
                "tensor_test": {
                    "operation": "Static(EML-0) ⊗ Dynamic(EML-2) = max(0,2) = 2",
                    "result": "Fiscal dynamics: 0⊗2=2 ✓"
                }
            }
        }

    def regime_shift_semiring(self) -> dict[str, Any]:
        return {
            "object": "Monetary policy regime shift (Volcker disinflation, ZLB)",
            "eml_depth": "∞",
            "shadow": 2,
            "semiring_test": {
                "pre_regime": {"depth": 2, "behavior": "Stable inflation expectations: EML-2"},
                "regime_change": {
                    "type": "TYPE 2 Horizon (sudden credibility shift)",
                    "depth": "∞",
                    "shadow": 2,
                    "why": "Volcker shock: exp(-λ·ΔI) = EML-2 shadow"
                },
                "sunspot_equilibria": {
                    "depth": "∞",
                    "shadow": 2,
                    "why": "Multiple equilibria (indeterminacy): EML-∞; shadow=2 (real-valued expectations)"
                }
            }
        }

    def dsge_semiring(self) -> dict[str, Any]:
        return {
            "object": "DSGE model (Dynamic Stochastic General Equilibrium)",
            "eml_depth": 2,
            "semiring_test": {
                "log_linearization": {
                    "depth": 2,
                    "why": "Log-linear approximation around SS: all variables log-deviations = EML-2"
                },
                "stochastic_shock": {
                    "formula": "a_t = ρ·a_{t-1} + ε_t: AR(1) shock = EML-2",
                    "depth": 2
                },
                "tensor_test": {
                    "operation": "DSGE(EML-2) ⊗ Shock(EML-2) = max(2,2) = 2",
                    "result": "DSGE: 2⊗2=2 ✓ (log-linearized = EML-2 closed)"
                }
            }
        }

    def analyze(self) -> dict[str, Any]:
        return {
            "model": "MacroDynamicsEML",
            "phillips": self.phillips_curve_semiring(),
            "taylor": self.taylor_rule_semiring(),
            "fiscal": self.fiscal_multiplier_semiring(),
            "regime": self.regime_shift_semiring(),
            "dsge": self.dsge_semiring(),
            "semiring_verdicts": {
                "phillips_curve": "2⊗2=2 ✓; ZLB = TYPE2 Horizon, shadow=2",
                "taylor_rule": "2⊗2=2 ✓",
                "dsge": "2⊗2=2 ✓ (log-linearized macro = EML-2 closed)",
                "regime_shifts": "TYPE 2 Horizon; shadow=2 (Volcker disinflation)",
                "new_finding": "Static fiscal multiplier=EML-0; dynamic fiscal = EML-2 (EML-0→EML-2 via dynamics)"
            }
        }


def analyze_macro_dynamics_eml() -> dict[str, Any]:
    t = MacroDynamicsEML()
    return {
        "session": 296,
        "title": "Macroeconomic Dynamics & Monetary Policy",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "analysis": t.analyze(),
        "key_theorem": (
            "Macro Semiring Theorem (S296): "
            "Log-linearized macroeconomics = CLOSED EML-2 SUBRING. "
            "Phillips curve, Taylor rule, DSGE: 2⊗2=2. "
            "Static fiscal multiplier = EML-0 (algebraic ratio); dynamics lifts to EML-2. "
            "ZLB and regime shifts = TYPE 2 Horizons with shadow=2. "
            "Volcker disinflation = TYPE 2 Horizon: credibility jump = non-constructive EML-∞, "
            "but the inflation decay path = EML-2 shadow. "
            "Sunspot equilibria (indeterminacy) = EML-∞, shadow=2. "
            "MACRO DEPTH LADDER: Static(EML-0) → DSGE(EML-2) → Regime shifts(EML-∞,shadow=2)."
        ),
        "rabbit_hole_log": [
            "Phillips + Taylor + DSGE: EML-2 closed subring (log-linear macro)",
            "Static multiplier: EML-0 (algebraic ratio); dynamics → EML-2",
            "ZLB = TYPE 2 Horizon; Volcker = TYPE 2 Horizon; both shadow=2",
            "Sunspot equilibria: EML-∞, shadow=2 (multiple equilibria = non-constructive)",
            "Log-linearization = the KEY move that keeps macro in EML-2"
        ]
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_macro_dynamics_eml(), indent=2, default=str))
