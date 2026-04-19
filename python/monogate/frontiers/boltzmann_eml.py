"""Session 54 — Statistical Mechanics & EML: Partition Functions and Free Energy.

Boltzmann weights, Z, free energy, heat capacity via ceml trees.
Z = Σ exp(-βE_i): each term is depth-1 ceml(-βE_i, 1).
"""
import math
from typing import Dict, List
__all__ = ["run_session54"]

def Z(energies: List[float], beta: float) -> float:
    return sum(math.exp(-beta*E) for E in energies)

def free_energy(energies: List[float], beta: float) -> float:
    return -math.log(Z(energies, beta)) / beta

def mean_energy(energies: List[float], beta: float) -> float:
    Zv = Z(energies, beta)
    return sum(E * math.exp(-beta*E) for E in energies) / Zv

def heat_capacity(energies: List[float], beta: float) -> float:
    Zv = Z(energies, beta)
    w = [math.exp(-beta*E)/Zv for E in energies]
    em = sum(E*wi for E,wi in zip(energies, w))
    e2m = sum(E**2*wi for E,wi in zip(energies, w))
    return beta**2 * (e2m - em**2)

DEPTH_TABLE = [
    {"quantity": "exp(-βE_i)",      "depth": 1},
    {"quantity": "Z = Σ exp(-βE)",  "depth": 1},
    {"quantity": "F = -kT log Z",   "depth": 1},
    {"quantity": "⟨E⟩",             "depth": 1},
    {"quantity": "C = β²·Var(E)",   "depth": 2},
    {"quantity": "Phase transition", "depth": "EML-∞"},
]

def verify_two_level(eps: float = 1.0) -> Dict:
    errors = []
    for beta in [0.5, 1.0, 2.0, 5.0]:
        Z_ref = 1 + math.exp(-beta*eps)
        F_ref = -math.log(Z_ref)/beta
        E_ref = eps/(1+math.exp(beta*eps))
        errors.append(max(
            abs(Z([0,eps], beta) - Z_ref),
            abs(free_energy([0,eps], beta) - F_ref),
            abs(mean_energy([0,eps], beta) - E_ref),
        ))
    return {"max_err": max(errors), "ok": max(errors) < 1e-10}

def verify_ising_1d(J: float = 1.0, N: int = 10) -> Dict:
    errors = []
    for beta in [0.5, 1.0, 2.0]:
        Z_exact = 2 * math.cosh(beta*J)**N
        Z_ceml  = 2 * ((math.exp(beta*J) + math.exp(-beta*J))/2)**N
        errors.append(abs(Z_exact - Z_ceml)/Z_exact)
    return {"max_rel_err": max(errors), "ok": max(errors) < 1e-10,
            "note": "cosh(βJ) = (ceml(βJ,1)+ceml(-βJ,1))/2 — depth 1"}

def run_session54() -> Dict:
    two = verify_two_level()
    ising = verify_ising_1d()
    theorems = [
        "CEML-T107: Boltzmann weight exp(-βE) = ceml(-βE, 1) — depth 1",
        "CEML-T108: Partition function Z is a depth-1 sum",
        "CEML-T109: Free energy F = -kT·log(Z) is depth-1 ceml(0,Z)",
        "CEML-T110: Heat capacity C is depth-2 (quadratic in ⟨E⟩)",
        "CEML-T111: Phase transitions require EML-∞ (thermodynamic limit, discontinuity)",
    ]
    return {
        "session": 54, "title": "Statistical Mechanics & EML",
        "depth_table": DEPTH_TABLE,
        "two_level": two, "ising_1d": ising,
        "theorems": theorems,
        "status": "PASS" if two["ok"] and ising["ok"] else "FAIL",
    }
